"""Face tracking and the 9:16 camera: where to point the crop and how far to zoom, per frame."""
from __future__ import annotations

import math
from pathlib import Path

import cv2
import numpy as np


def _detector():
    path = Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"
    det = cv2.CascadeClassifier(str(path))
    if det.empty():
        raise RuntimeError(f"Could not load face detector at {path}. Install opencv-python-headless<5.")
    return det


def track_faces(video: Path, every: int = 3, detect_width: int = 640) -> tuple[list[tuple[float, float] | None], float, int, int]:
    """Return per-frame face centre (normalised 0-1) or None, plus fps and size."""
    cap = cv2.VideoCapture(str(video))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    det = _detector()
    scale = detect_width / max(1, w)
    centres: list[tuple[float, float] | None] = []
    prev: tuple[float, float] | None = None
    i = 0
    last: tuple[float, float] | None = None
    while True:
        ok = cap.grab()
        if not ok:
            break
        if i % every == 0:
            ok, frame = cap.retrieve()
            if not ok:
                break
            small = cv2.resize(frame, (detect_width, max(1, int(h * scale))))
            gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
            faces = det.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=6,
                                         minSize=(max(24, int(detect_width * 0.035)),) * 2)
            last = None
            if len(faces):
                # Prefer big faces, and the one nearest the previous face so the camera does not jump.
                def score(f):
                    fx, fy, fw, fh = f
                    cx, cy = (fx + fw / 2) / small.shape[1], (fy + fh / 2) / small.shape[0]
                    dist = math.hypot(cx - prev[0], cy - prev[1]) if prev else 0
                    return fw * fh / (small.shape[1] * small.shape[0]) - dist * 0.05

                fx, fy, fw, fh = max(faces, key=score)
                last = ((fx + fw / 2) / small.shape[1], (fy + fh * 0.45) / small.shape[0])
                prev = last
        centres.append(last)
        i += 1
    cap.release()
    return centres, fps, w, h


def smooth_path(raw: list[tuple[float, float] | None], fps: float, alpha: float = 0.12,
                deadzone: float = 0.03) -> tuple[np.ndarray, list[float]]:
    """Fill gaps, smooth the camera, and return speaker-switch times (seconds)."""
    n = len(raw)
    if n == 0:
        return np.zeros((0, 2)), []
    filled = np.full((n, 2), np.nan)
    for i, c in enumerate(raw):
        if c is not None:
            filled[i] = c
    # hold last known value, back-fill the start, default to the centre
    last = None
    for i in range(n):
        if not np.isnan(filled[i, 0]):
            last = filled[i].copy()
        elif last is not None:
            filled[i] = last
    first = next((filled[i] for i in range(n) if not np.isnan(filled[i, 0])), np.array([0.5, 0.4]))
    filled[np.isnan(filled[:, 0])] = first

    out = np.zeros_like(filled)
    cam = filled[0].copy()
    switches: list[float] = []
    jump_since: int | None = None
    hold = int(fps * 0.4)
    for i in range(n):
        target = filled[i]
        diff = target - cam
        if abs(diff[0]) > 0.22:  # a different person: wait a moment to be sure, then cut-move fast
            jump_since = i if jump_since is None else jump_since
            if i - jump_since >= hold:
                switches.append(i / fps)
                cam = cam + diff * 0.5
                jump_since = None
        else:
            jump_since = None
            if abs(diff[0]) > deadzone or abs(diff[1]) > deadzone:
                cam = cam + diff * alpha
        out[i] = cam
    return out, switches


def _ease(x: float) -> float:
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def zoom_curve(n: int, fps: float, base: float, events: list[dict]) -> np.ndarray:
    """Base zoom with a slow push-in, plus smooth punch-ins for each event {t, scale, dur}."""
    t = np.arange(n) / fps
    duration = max(t[-1] if n else 1.0, 1e-3)
    z = base * (1.0 + 0.05 * (t / duration))  # gentle push-in keeps the frame alive
    for e in events:
        start = float(e["t"])
        scale = float(e.get("scale", 1.25))
        dur = float(e.get("dur", 1.2))
        up, down = 0.3, 0.5
        boost = np.zeros(n)
        for i, ti in enumerate(t):
            if ti < start or ti > start + up + dur + down:
                continue
            if ti < start + up:
                k = _ease((ti - start) / up)
            elif ti < start + up + dur:
                k = 1.0
            else:
                k = 1.0 - _ease((ti - start - up - dur) / down)
            boost[i] = k
        z = np.maximum(z, z * (1 + (scale - 1) * boost))
    return z


def crop_face(frame: np.ndarray, centre: np.ndarray, zoom: float, out_w: int, out_h: int) -> np.ndarray:
    h, w = frame.shape[:2]
    target_ratio = out_w / out_h
    crop_h = h / zoom
    crop_w = crop_h * target_ratio
    if crop_w > w:  # very narrow source: fit width instead
        crop_w = w / zoom
        crop_h = crop_w / target_ratio
    cx = min(max(centre[0] * w, crop_w / 2), w - crop_w / 2)
    cy = min(max(centre[1] * h, crop_h / 2), h - crop_h / 2)
    x0, y0 = int(round(cx - crop_w / 2)), int(round(cy - crop_h / 2))
    crop = frame[y0:y0 + int(crop_h), x0:x0 + int(crop_w)]
    return cv2.resize(crop, (out_w, out_h), interpolation=cv2.INTER_LINEAR)


def fit_blur(frame: np.ndarray, zoom: float, out_w: int, out_h: int) -> np.ndarray:
    """Whole frame in the middle over a blurred, darker copy (good for gameplay or wide shots)."""
    h, w = frame.shape[:2]
    bg_scale = out_h / h
    bg = cv2.resize(frame, (int(w * bg_scale), out_h))
    x0 = (bg.shape[1] - out_w) // 2
    bg = bg[:, x0:x0 + out_w]
    small = cv2.resize(bg, (out_w // 8, out_h // 8), interpolation=cv2.INTER_AREA)
    small = cv2.GaussianBlur(small, (0, 0), 4)
    bg = cv2.resize((small * 0.55).astype(np.uint8), (out_w, out_h), interpolation=cv2.INTER_LINEAR)
    fg_w = int(out_w * zoom)
    fg_h = int(h * fg_w / w)
    fg = cv2.resize(frame, (fg_w, fg_h))
    if fg_w > out_w:
        cx = (fg_w - out_w) // 2
        fg = fg[:, cx:cx + out_w]
        fg_w = out_w
    y = (out_h - fg_h) // 2
    x = (out_w - fg_w) // 2
    y0, y1 = max(0, y), min(out_h, y + fg_h)
    bg[y0:y1, x:x + fg_w] = fg[y0 - y:y1 - y]
    return bg
