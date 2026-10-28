"""Finding and running ffmpeg on Windows (and Linux)."""
from __future__ import annotations

import shutil
import subprocess
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def ffmpeg_bin() -> str:
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg  # pip fallback that ships its own binary

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:  # pragma: no cover - depends on machine
        raise SystemExit(
            "ffmpeg was not found. Install it with "
            "`winget install Gyan.FFmpeg` or `pip install imageio-ffmpeg`."
        ) from exc


def run(args: list[str], quiet: bool = True) -> None:
    cmd = [ffmpeg_bin(), "-hide_banner", "-y"]
    if quiet:
        cmd += ["-loglevel", "error"]
    cmd += [str(a) for a in args]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed ({result.returncode}):\n{' '.join(cmd)}\n{result.stderr[-3000:]}")


def extract_audio(src: Path, dst: Path, rate: int = 16000, start: float | None = None,
                  duration: float | None = None, channels: int = 1) -> Path:
    args: list[str] = []
    if start is not None:
        args += ["-ss", f"{start:.3f}"]
    args += ["-i", src]
    if duration is not None:
        args += ["-t", f"{duration:.3f}"]
    args += ["-vn", "-ac", str(channels), "-ar", str(rate), "-c:a", "pcm_s16le", dst]
    run(args)
    return dst


def cut_video(src: Path, dst: Path, start: float, duration: float) -> Path:
    """Frame-accurate cut, re-encoded fast so OpenCV can read it from frame 0."""
    run([
        "-ss", f"{start:.3f}", "-i", src, "-t", f"{duration:.3f}",
        "-map", "0:v:0", "-map", "0:a:0?",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "16", "-pix_fmt", "yuv420p",
        "-c:a", "pcm_s16le", "-ar", "48000", "-ac", "2", dst,
    ])
    return dst


def open_raw_writer(dst: Path, width: int, height: int, fps: float, crf: int, preset: str) -> subprocess.Popen:
    """Start an ffmpeg process that encodes raw BGR frames written to its stdin."""
    cmd = [
        ffmpeg_bin(), "-hide_banner", "-loglevel", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{width}x{height}", "-r", f"{fps:.3f}", "-i", "-",
        "-an", "-c:v", "libx264", "-preset", preset, "-crf", str(crf), "-pix_fmt", "yuv420p",
        str(dst),
    ]
    return subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
