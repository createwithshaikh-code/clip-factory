"""Music by mood, sound effects on cue, commentary voice, all mixed with ffmpeg."""
from __future__ import annotations

import hashlib
import random
from pathlib import Path

from .config import AUDIO_EXTS, MUSIC_DIR, SFX_DIR, ROOT
from .ffmpeg import run
from .voice import wav_duration


def _audio_files(folder: Path) -> list[Path]:
    if not folder.exists():
        return []
    return sorted(p for p in folder.rglob("*") if p.suffix.lower() in AUDIO_EXTS)


def _folder(setting: str, default: Path) -> Path:
    if not setting:
        return default
    p = Path(setting).expanduser()
    return p if p.is_absolute() else ROOT / p


def pick_music(mood: str, profile: dict, seed: str) -> Path | None:
    base = _folder(profile["music"].get("folder", ""), MUSIC_DIR)
    files = _audio_files(base / mood) or _audio_files(base)
    if not files:
        return None
    return random.Random(hashlib.md5(seed.encode()).hexdigest()).choice(files)


def find_sfx(name: str, profile: dict) -> Path | None:
    for folder in (_folder(profile["sfx"].get("folder", ""), SFX_DIR), SFX_DIR):
        for ext in AUDIO_EXTS:
            p = folder / f"{name}{ext}"
            if p.exists():
                return p
        matches = [p for p in _audio_files(folder) if p.stem.lower() == name.lower()]
        if matches:
            return matches[0]
    return None


def available_sfx(profile: dict) -> list[str]:
    names = {p.stem for p in _audio_files(_folder(profile["sfx"].get("folder", ""), SFX_DIR))}
    names |= {p.stem for p in _audio_files(SFX_DIR)}
    return sorted(names)


def mix(clip_media: Path, duration: float, clip: dict, profile: dict, voice_wav: Path | None,
        out_audio: Path, has_audio: bool = True) -> Path:
    inputs: list[list[str]] = []
    filters: list[str] = []
    labels: list[str] = []

    voice_start = float(clip.get("commentary_at", 0.0))
    voice_len = wav_duration(voice_wav) if voice_wav else 0.0
    duck = f"between(t,{voice_start:.2f},{voice_start + voice_len + 0.2:.2f})"

    # 0: original audio of the clip
    if has_audio:
        inputs.append(["-i", str(clip_media)])
        orig = f"[0:a]aresample=48000,volume={profile['original_audio']['volume']}"
        if voice_wav:
            orig += f",volume={profile['original_audio']['duck_during_commentary']}:enable='{duck}'"
        filters.append(orig + "[orig]")
    else:
        inputs.append(["-f", "lavfi", "-t", f"{duration:.3f}", "-i", "anullsrc=r=48000:cl=stereo"])
        filters.append("[0:a]anull[orig]")
    labels.append("[orig]")

    idx = 1
    if profile["music"].get("enabled", True):
        track = pick_music(clip.get("mood", "hype"), profile, clip["id"] + str(clip.get("start")))
        if track:
            offset = random.Random(clip["id"]).uniform(0, 20)
            inputs.append(["-stream_loop", "-1", "-ss", f"{offset:.2f}", "-i", str(track)])
            vol = float(profile["music"].get("volume", 0.12))
            m = (f"[{idx}:a]aresample=48000,atrim=0:{duration:.3f},asetpts=N/SR/TB,volume={vol},"
                 f"afade=t=in:d=0.6,afade=t=out:st={max(0.0, duration - 1.2):.2f}:d=1.2")
            if voice_wav:
                m += f",volume=0.5:enable='{duck}'"
            filters.append(m + "[music]")
            labels.append("[music]")
            idx += 1
            print(f"  music: {track.name}")
        else:
            print(f"  (no music in assets/music/{clip.get('mood', 'hype')} - add some tracks)")

    if profile["sfx"].get("enabled", True):
        svol = float(profile["sfx"].get("volume", 0.9))
        for s in clip.get("sfx", []):
            path = find_sfx(s["name"], profile)
            if not path:
                print(f"  (sfx '{s['name']}' not found in assets/sfx, skipped)")
                continue
            ms = int(float(s["t"]) * 1000)
            inputs.append(["-i", str(path)])
            vol = float(s.get("volume", svol))
            filters.append(f"[{idx}:a]aresample=48000,volume={vol},adelay={ms}|{ms}[s{idx}]")
            labels.append(f"[s{idx}]")
            idx += 1

    if voice_wav:
        ms = int(voice_start * 1000)
        inputs.append(["-i", str(voice_wav)])
        vvol = float(profile["commentary"].get("volume", 1.0))
        filters.append(f"[{idx}:a]aresample=48000,volume={vvol},adelay={ms}|{ms}[voice]")
        labels.append("[voice]")
        idx += 1

    filters.append(
        f"{''.join(labels)}amix=inputs={len(labels)}:duration=first:normalize=0,"
        f"alimiter=limit=0.95,atrim=0:{duration:.3f}[out]"
    )
    args: list[str] = []
    for i in inputs:
        args += i
    args += ["-filter_complex", ";".join(filters), "-map", "[out]", "-c:a", "aac", "-b:a", "192k", str(out_audio)]
    run(args)
    return out_audio
