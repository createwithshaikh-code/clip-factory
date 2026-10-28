"""Captions and hook text drawn with Pillow (no libass, so it behaves the same on every OS)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageColor, ImageDraw, ImageFont


def _rgb(color: str) -> tuple[int, int, int]:
    return ImageColor.getrgb(color)[:3]


@lru_cache(maxsize=64)
def _font(path: str | None, size: int) -> ImageFont.FreeTypeFont:
    if path:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default(size=size)


def group_words(words: list[dict], per_line: int, max_gap: float = 0.6) -> list[dict]:
    """Split words into short caption groups: {start, end, words:[...]}"""
    groups: list[dict] = []
    cur: list[dict] = []
    for w in words:
        if cur and (len(cur) >= per_line or w["start"] - cur[-1]["end"] > max_gap):
            groups.append(cur)
            cur = []
        cur.append(w)
    if cur:
        groups.append(cur)
    out = []
    for i, g in enumerate(groups):
        end = g[-1]["end"]
        if i + 1 < len(groups):
            nxt = groups[i + 1][0]["start"]
            if nxt - end < 0.4:
                end = nxt  # no flicker between groups
        out.append({"start": g[0]["start"], "end": end + (0 if i + 1 < len(groups) else 0.3), "words": g})
    return out


class CaptionRenderer:
    def __init__(self, cfg: dict, font_path: Path | None, frame_w: int, frame_h: int):
        self.cfg = cfg
        self.font_path = str(font_path) if font_path else None
        self.w = frame_w
        self.h = frame_h
        self._cache: dict[tuple[int, int], tuple[np.ndarray, int, int]] = {}

    def _text(self, word: str) -> str:
        return word.upper() if self.cfg.get("uppercase", True) else word

    def _render(self, group: dict, active: int) -> tuple[np.ndarray, int, int]:
        cfg = self.cfg
        words = [self._text(w["word"]) for w in group["words"]]
        size = int(cfg.get("size", 86))
        stroke = int(cfg.get("stroke_width", 7))
        max_w = int(self.w * 0.9)
        while True:
            font = _font(self.font_path, size)
            space = font.getlength(" ")
            widths = [font.getlength(t) for t in words]
            total = sum(widths) + space * (len(words) - 1) + stroke * 2
            if total <= max_w or size <= 36:
                break
            size = int(size * 0.9)
        ascent, descent = font.getmetrics()
        img_h = ascent + descent + stroke * 2 + 10
        img = Image.new("RGBA", (int(total) + 4, img_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        x = stroke
        for i, (t, wdt) in enumerate(zip(words, widths)):
            color = cfg.get("highlight") if i == active else cfg.get("color")
            draw.text((x, stroke + 4), t, font=font, fill=_rgb(color),
                      stroke_width=stroke, stroke_fill=_rgb(cfg.get("stroke", "#000000")))
            x += wdt + space
        arr = np.array(img)
        left = (self.w - arr.shape[1]) // 2
        top = int(self.h * float(cfg.get("y", 0.62)) - arr.shape[0] / 2)
        return arr, left, top

    def draw(self, frame: np.ndarray, groups: list[dict], t: float) -> None:
        for gi, g in enumerate(groups):
            if g["start"] <= t < g["end"]:
                active = 0
                for wi, w in enumerate(g["words"]):
                    if w["start"] <= t:
                        active = wi
                key = (gi, active)
                if key not in self._cache:
                    self._cache[key] = self._render(g, active)
                blend(frame, *self._cache[key])
                return


def render_hook(text: str, cfg: dict, font_path: Path | None, frame_w: int, frame_h: int) -> tuple[np.ndarray, int, int]:
    size = int(cfg.get("size", 68))
    font = _font(str(font_path) if font_path else None, size)
    max_w = int(frame_w * 0.84)
    words = text.split()
    lines: list[str] = []
    cur = ""
    for w in words:
        trial = f"{cur} {w}".strip()
        if font.getlength(trial) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    ascent, descent = font.getmetrics()
    line_h = ascent + descent + 6
    pad = 28
    box_w = int(max(font.getlength(line) for line in lines)) + pad * 2
    box_h = line_h * len(lines) + pad * 2
    img = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((0, 0, box_w - 1, box_h - 1), radius=26, fill=_rgb(cfg.get("background", "#FFFFFF")) + (240,))
    for i, line in enumerate(lines):
        lw = font.getlength(line)
        draw.text(((box_w - lw) / 2, pad + i * line_h), line, font=font, fill=_rgb(cfg.get("color", "#000000")))
    arr = np.array(img)
    left = (frame_w - box_w) // 2
    top = int(frame_h * float(cfg.get("y", 0.16)) - box_h / 2)
    return arr, left, top


def blend(frame: np.ndarray, rgba: np.ndarray, left: int, top: int, alpha_mul: float = 1.0) -> None:
    """Alpha-blend an RGBA image onto a BGR frame in place (clipped to the frame)."""
    fh, fw = frame.shape[:2]
    h, w = rgba.shape[:2]
    x0, y0 = max(0, left), max(0, top)
    x1, y1 = min(fw, left + w), min(fh, top + h)
    if x0 >= x1 or y0 >= y1:
        return
    sub = rgba[y0 - top:y1 - top, x0 - left:x1 - left]
    alpha = (sub[..., 3:4].astype(np.float32) / 255.0) * alpha_mul
    bgr = sub[..., 2::-1].astype(np.float32)
    region = frame[y0:y1, x0:x1].astype(np.float32)
    frame[y0:y1, x0:x1] = (bgr * alpha + region * (1 - alpha)).astype(np.uint8)
