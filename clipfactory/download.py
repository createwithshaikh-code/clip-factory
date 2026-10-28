"""Get source videos into work/<video_id>/ (from a URL with yt-dlp, or a local file)."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from .config import VIDEO_EXTS, slugify, work_dir_for
from .ffmpeg import ffmpeg_bin


def _write_meta(wd: Path, meta: dict) -> None:
    (wd / "meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")


def read_meta(wd: Path) -> dict:
    p = wd / "meta.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def download(url: str, channel: str, max_height: int = 1080) -> Path:
    try:
        import yt_dlp
    except ImportError as exc:
        raise SystemExit("yt-dlp is not installed: pip install -r requirements.txt") from exc

    with yt_dlp.YoutubeDL({"quiet": True, "skip_download": True}) as ydl:
        info = ydl.extract_info(url, download=False)
    video_id = f"{slugify(info.get('uploader') or 'src', 20)}-{slugify(info.get('id') or info.get('title') or 'video', 30)}"
    wd = work_dir_for(video_id)
    target = wd / "source.mp4"
    if not target.exists():
        opts = {
            "outtmpl": str(wd / "source.%(ext)s"),
            "format": f"bv*[height<={max_height}]+ba/b[height<={max_height}]/b",
            "merge_output_format": "mp4",
            "ffmpeg_location": ffmpeg_bin(),
            "quiet": False,
            "noprogress": False,
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
        if not target.exists():  # yt-dlp may keep another container
            for p in wd.glob("source.*"):
                if p.suffix.lower() in VIDEO_EXTS:
                    p.rename(target)
                    break
    _write_meta(wd, {
        "video_id": video_id,
        "channel": channel,
        "url": url,
        "title": info.get("title"),
        "uploader": info.get("uploader"),
        "duration": info.get("duration"),
        "source": "source.mp4",
    })
    print(f"Downloaded -> {target}")
    return wd


def ingest_local(path: Path, channel: str, copy: bool = False) -> Path:
    path = path.expanduser().resolve()
    if not path.exists():
        raise SystemExit(f"File not found: {path}")
    video_id = slugify(path.stem, 50)
    wd = work_dir_for(video_id)
    source = str(path)
    if copy:
        dst = wd / f"source{path.suffix.lower()}"
        if not dst.exists():
            shutil.copy2(path, dst)
        source = dst.name
    _write_meta(wd, {
        "video_id": video_id,
        "channel": channel,
        "url": None,
        "title": path.stem,
        "uploader": None,
        "duration": None,
        "source": source,
    })
    return wd


def source_path(wd: Path) -> Path:
    meta = read_meta(wd)
    src = Path(meta.get("source", "source.mp4"))
    return src if src.is_absolute() else wd / src
