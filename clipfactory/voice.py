"""Commentary voice-over.

engine options (channel YAML -> commentary.engine):
  none    no voice; the commentary text is still shown on screen as the hook
  elevenlabs  Claude Code makes the voice with the ElevenLabs MCP and saves it as
              work/<video_id>/voice/<clip_id>.mp3 (see docs/ELEVENLABS.md)
  file    you record it yourself: work/<video_id>/voice/<clip_id>.wav|.mp3|.m4a
  system  the computer's built-in voice (macOS `say`, Windows SAPI via PowerShell)
  piper   free local neural voice: https://github.com/rhasspy/piper  (set commentary.voice to the .onnx model)
"""
from __future__ import annotations

import platform
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

from .config import AUDIO_EXTS
from .ffmpeg import run


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as wf:
        return wf.getnframes() / float(wf.getframerate())


def _to_wav(src: Path, dst: Path) -> Path:
    run(["-i", src, "-ac", "2", "-ar", "48000", "-c:a", "pcm_s16le", dst])
    return dst


def _system_tts(text: str, raw: Path, voice: str, rate: int) -> Path:
    system = platform.system()
    if system == "Darwin":
        out = raw.with_suffix(".aiff")
        cmd = ["say", "-o", str(out), "-r", str(rate)]
        if voice:
            cmd += ["-v", voice]
        subprocess.run(cmd + [text], check=True)
        return out
    if system == "Windows":
        out = raw.with_suffix(".wav")
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as f:
            f.write(text)
            text_file = f.name
        sapi_rate = max(-10, min(10, int((rate - 180) / 15)))
        ps = (
            "Add-Type -AssemblyName System.Speech; "
            "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            + (f"$s.SelectVoice('{voice}'); " if voice else "")
            + f"$s.Rate = {sapi_rate}; "
            f"$s.SetOutputToWaveFile('{out}'); "
            f"$s.Speak([IO.File]::ReadAllText('{text_file}')); $s.Dispose()"
        )
        subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)
        Path(text_file).unlink(missing_ok=True)
        return out
    espeak = shutil.which("espeak-ng") or shutil.which("espeak")
    if not espeak:
        raise RuntimeError("No system voice found (install espeak-ng on Linux).")
    out = raw.with_suffix(".wav")
    subprocess.run([espeak, "-s", str(rate), "-w", str(out), text], check=True)
    return out


def _piper(text: str, raw: Path, model: str) -> Path:
    exe = shutil.which("piper")
    if not exe or not model:
        raise RuntimeError("piper engine needs the `piper` command on PATH and commentary.voice = path to a .onnx voice")
    out = raw.with_suffix(".wav")
    subprocess.run([exe, "--model", model, "--output_file", str(out)], input=text.encode("utf-8"), check=True)
    return out


def commentary_audio(clip: dict, wd: Path, cfg: dict) -> Path | None:
    """Return a 48 kHz stereo wav for the clip's commentary, or None."""
    engine = (cfg.get("engine") or "none").lower()
    text = (clip.get("commentary") or "").strip()
    voice_dir = wd / "voice"
    voice_dir.mkdir(exist_ok=True)
    final = voice_dir / f"{clip['id']}.mix.wav"

    if engine in ("file", "elevenlabs"):
        for ext in AUDIO_EXTS:
            p = voice_dir / f"{clip['id']}{ext}"
            if p.exists():
                return _to_wav(p, final)
        print(f"  (no voice file at {voice_dir / (clip['id'] + '.mp3')}, skipping voice)")
        return None
    if engine == "none" or not text:
        return None
    raw = voice_dir / f"{clip['id']}.tts"
    try:
        if engine == "system":
            produced = _system_tts(text, raw, cfg.get("voice", ""), int(cfg.get("rate", 185)))
        elif engine == "piper":
            produced = _piper(text, raw, cfg.get("voice", ""))
        else:
            raise RuntimeError(f"unknown commentary engine '{engine}'")
    except Exception as exc:
        print(f"  (voice failed: {exc}; continuing without voice)")
        return None
    return _to_wav(produced, final)
