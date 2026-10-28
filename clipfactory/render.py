"""Turn one plan.json into finished vertical clips."""
from __future__ import annotations

import json
import shutil
import subprocess
import time
from datetime import date
from pathlib import Path

import cv2

from . import audio, overlay, reframe
from .config import OUTPUT_DIR, load_channel, resolve_font
from .download import read_meta, source_path
from .ffmpeg import cut_video, ffmpeg_bin, open_raw_writer, run
from .plan import load_plan
from .transcribe import words_between
from .voice import commentary_audio


def _has_audio(media: Path) -> bool:
    r = subprocess.run([ffmpeg_bin(), "-hide_banner", "-i", str(media)], capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    return "Audio:" in r.stderr


def render_clip(clip: dict, wd: Path, source: Path, transcript: dict, profile: dict, out_dir: Path,
                keep_temp: bool = False) -> Path:
    t0 = time.time()
    vcfg = profile["video"]
    out_w, out_h, fps_out = int(vcfg["width"]), int(vcfg["height"]), float(vcfg["fps"])
    start, end = float(clip["start"]), float(clip["end"])
    duration = end - start
    tmp = wd / "tmp" / clip["id"]
    tmp.mkdir(parents=True, exist_ok=True)

    print(f"[{clip['id']}] {clip.get('title', '')}  ({start:.1f}s-{end:.1f}s, {duration:.1f}s)")
    cut = cut_video(source, tmp / "cut.mkv", start, duration)

    layout = clip.get("layout") or profile.get("layout", "face")
    cap = cv2.VideoCapture(str(cut))
    src_fps = cap.get(cv2.CAP_PROP_FPS) or fps_out
    n_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or int(duration * src_fps)
    cap.release()

    switches: list[float] = []
    if layout == "face":
        raw, src_fps, _, _ = reframe.track_faces(cut)
        n_frames = len(raw)
        path, switches = reframe.smooth_path(raw, src_fps, float(profile["zoom"].get("smoothing", 0.12)))
        found = sum(1 for r in raw if r is not None)
        print(f"  face found in {found * 100 // max(1, len(raw))}% of frames, {len(switches)} speaker changes")
    else:
        path = None

    events = list(clip.get("zooms", []))
    punch = float(profile["zoom"].get("speaker_change_punch", 1.12))
    if punch > 1.0:
        events += [{"t": s, "scale": punch, "dur": 0.9} for s in switches]
    explicit = [float(z["t"]) for z in clip.get("zooms", [])]
    for s in clip.get("sfx", []):  # every sound hit gets a small visual punch unless one is planned
        if all(abs(float(s["t"]) - t) > 0.5 for t in explicit):
            events.append({"t": float(s["t"]), "scale": 1.08, "dur": 0.25})
    zoom = reframe.zoom_curve(n_frames, src_fps, float(profile["zoom"].get("base", 1.0)), events)

    font = resolve_font(profile["captions"].get("font", ""))
    groups = []
    if profile["captions"].get("enabled", True):
        words = words_between(transcript, start, end)
        groups = overlay.group_words(words, int(profile["captions"].get("words_per_line", 3)))
    captions = overlay.CaptionRenderer(profile["captions"], font, out_w, out_h)
    hook = None
    hook_text = (clip.get("hook_text") or "").strip()
    if hook_text and profile["hook"].get("enabled", True):
        hook = overlay.render_hook(hook_text, profile["hook"], font, out_w, out_h)
    hook_secs = float(profile["hook"].get("seconds", 3.0))

    video_only = tmp / "video.mp4"
    writer = open_raw_writer(video_only, out_w, out_h, src_fps, int(vcfg["crf"]), vcfg["preset"])
    cap = cv2.VideoCapture(str(cut))
    i = 0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            z = float(zoom[min(i, len(zoom) - 1)]) if len(zoom) else 1.0
            if layout == "face" and path is not None and len(path):
                out = reframe.crop_face(frame, path[min(i, len(path) - 1)], z, out_w, out_h)
            else:
                out = reframe.fit_blur(frame, z, out_w, out_h)
            t = i / src_fps
            captions.draw(out, groups, t)
            if hook and t < hook_secs:
                fade = min(1.0, (hook_secs - t) / 0.3)
                overlay.blend(out, *hook, alpha_mul=fade)
            writer.stdin.write(out.tobytes())
            i += 1
    finally:
        cap.release()
        writer.stdin.close()
        err = writer.stderr.read().decode("utf-8", "replace")
        if writer.wait() != 0:
            raise RuntimeError(f"video encode failed: {err[-2000:]}")

    voice = commentary_audio(clip, wd, profile["commentary"])
    mixed = audio.mix(cut, duration, clip, profile, voice, tmp / "audio.m4a", has_audio=_has_audio(cut))

    out_dir.mkdir(parents=True, exist_ok=True)
    base = f"{date.today():%Y%m%d}_{wd.name}_{clip['id']}"
    final = out_dir / f"{base}.mp4"
    run(["-i", video_only, "-i", mixed, "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "copy",
         "-movflags", "+faststart", "-shortest", final])
    _write_upload_notes(final.with_suffix(".txt"), clip, read_meta(wd))
    if not keep_temp:
        shutil.rmtree(tmp, ignore_errors=True)
    print(f"  -> {final}  ({time.time() - t0:.0f}s)")
    return final


def _write_upload_notes(path: Path, clip: dict, meta: dict) -> None:
    tags = " ".join(clip.get("hashtags", []))
    credit = ""
    if meta.get("uploader") or meta.get("url"):
        credit = f"\n\nOriginal: {meta.get('uploader') or ''} {meta.get('url') or ''}".rstrip()
    body = (
        f"TITLE:\n{clip.get('title', '')}\n\n"
        f"DESCRIPTION:\n{clip.get('description', '')}{credit}\n\n{tags}\n\n"
        f"COMMENTARY:\n{clip.get('commentary', '')}\n"
    )
    path.write_text(body, encoding="utf-8")


def render_plan(plan_path: Path, only: list[str] | None = None, keep_temp: bool = False) -> list[Path]:
    plan_path = Path(plan_path).resolve()
    plan = load_plan(plan_path)
    wd = plan_path.parent
    meta = read_meta(wd)
    channel = plan.get("channel") or meta.get("channel")
    if not channel:
        raise SystemExit("plan.json has no 'channel' and meta.json has none either")
    profile = load_channel(channel)
    source = source_path(wd)
    tpath = wd / "transcript.json"
    transcript = json.loads(tpath.read_text(encoding="utf-8")) if tpath.exists() else {"segments": []}
    out_dir = OUTPUT_DIR / channel
    done = []
    for clip in plan["clips"]:
        if only and clip["id"] not in only:
            continue
        done.append(render_clip(clip, wd, source, transcript, profile, out_dir, keep_temp))
    print(f"\nRendered {len(done)} clip(s) into {out_dir}")
    return done
