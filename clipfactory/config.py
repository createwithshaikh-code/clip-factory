"""Paths, channel profiles and small helpers shared by every step."""
from __future__ import annotations

import copy
import os
import platform
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CHANNELS_DIR = ROOT / "channels"
ASSETS_DIR = ROOT / "assets"
MUSIC_DIR = ASSETS_DIR / "music"
SFX_DIR = ASSETS_DIR / "sfx"
FONTS_DIR = ASSETS_DIR / "fonts"
WORK_DIR = ROOT / "work"
OUTPUT_DIR = ROOT / "output"

AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".aac", ".ogg", ".flac"}
VIDEO_EXTS = {".mp4", ".mkv", ".mov", ".webm", ".avi", ".flv", ".ts"}

# Defaults for every channel. A channel YAML only lists what it changes.
DEFAULT_PROFILE: dict = {
    "name": "default",
    "niche": "",
    "language": "en",
    "sources": [],
    "clip": {"min_seconds": 20, "max_seconds": 45, "target_seconds": 30},
    "video": {"width": 1080, "height": 1920, "fps": 30, "crf": 20, "preset": "medium"},
    "layout": "face",  # face | fit_blur
    "captions": {
        "enabled": True,
        "font": "",  # file name in assets/fonts, or an absolute path; empty = system bold font
        "size": 86,
        "words_per_line": 3,
        "uppercase": True,
        "y": 0.62,  # vertical centre of the caption, 0 = top, 1 = bottom
        "color": "#FFFFFF",
        "highlight": "#FFE600",
        "stroke": "#000000",
        "stroke_width": 7,
    },
    "hook": {
        "enabled": True,
        "seconds": 3.0,
        "size": 68,
        "y": 0.16,
        "color": "#000000",
        "background": "#FFFFFF",
    },
    "zoom": {"base": 1.0, "speaker_change_punch": 1.12, "smoothing": 0.12},
    "music": {"enabled": True, "volume": 0.12, "folder": ""},  # folder overrides assets/music
    "sfx": {"enabled": True, "volume": 0.9, "folder": ""},
    "original_audio": {"volume": 1.0, "duck_during_commentary": 0.25},
    "commentary": {"engine": "none", "voice": "", "rate": 185, "volume": 1.0},
    "transcribe": {"model": "small", "device": "auto"},
}


def deep_merge(base: dict, extra: dict) -> dict:
    out = copy.deepcopy(base)
    for key, value in (extra or {}).items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def list_channels() -> list[str]:
    return sorted(p.stem for p in CHANNELS_DIR.glob("*.yaml") if not p.stem.startswith("_"))


def load_channel(name: str) -> dict:
    path = CHANNELS_DIR / f"{name}.yaml"
    if not path.exists():
        raise SystemExit(
            f"Channel '{name}' not found in {CHANNELS_DIR}. Available: {', '.join(list_channels()) or 'none'}"
        )
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    profile = deep_merge(DEFAULT_PROFILE, data)
    profile["slug"] = name
    return profile


def slugify(text: str, limit: int = 60) -> str:
    text = re.sub(r"[^\w\s-]", "", text, flags=re.UNICODE).strip().lower()
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:limit].strip("-") or "video"


def work_dir_for(video_id: str) -> Path:
    d = WORK_DIR / video_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def system_font_candidates() -> list[Path]:
    system = platform.system()
    if system == "Windows":
        windir = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
        names = ["impact.ttf", "arialbd.ttf", "seguibl.ttf", "segoeuib.ttf", "verdanab.ttf"]
        return [windir / n for n in names]
    return [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
    ]


def resolve_font(font: str) -> Path | None:
    """Return a usable .ttf/.otf path: channel setting, then assets/fonts, then the OS."""
    if font:
        p = Path(font)
        if not p.is_absolute():
            p = FONTS_DIR / font
        if p.exists():
            return p
    bundled = sorted(list(FONTS_DIR.glob("*.ttf")) + list(FONTS_DIR.glob("*.otf")))
    if bundled:
        return bundled[0]
    for p in system_font_candidates():
        if p.exists():
            return p
    return None
