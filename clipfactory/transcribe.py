"""Local speech-to-text (faster-whisper) and the loudness map used to spot hype moments."""
from __future__ import annotations

import json
import wave
from pathlib import Path

import numpy as np

from .ffmpeg import extract_audio


def _pick_device(device: str) -> tuple[str, str]:
    if device not in ("auto", ""):
        return device, "float16" if device == "cuda" else "int8"
    try:
        import ctranslate2

        if ctranslate2.get_cuda_device_count() > 0:
            return "cuda", "float16"
    except Exception:
        pass
    return "cpu", "int8"


def transcribe(audio_wav: Path, out_json: Path, model_name: str = "small", language: str | None = "en",
               device: str = "auto") -> dict:
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise SystemExit("faster-whisper is not installed: pip install -r requirements.txt") from exc

    dev, compute = _pick_device(device)
    print(f"Transcribing with whisper '{model_name}' on {dev} ({compute}). First run downloads the model.")
    model = WhisperModel(model_name, device=dev, compute_type=compute)
    segments, info = model.transcribe(
        str(audio_wav), language=language or None, word_timestamps=True, vad_filter=True, beam_size=5,
    )
    data = {"language": info.language, "duration": info.duration, "segments": []}
    for seg in segments:
        words = [
            {"start": round(w.start, 2), "end": round(w.end, 2), "word": w.word.strip()}
            for w in (seg.words or []) if w.word.strip()
        ]
        data["segments"].append({
            "start": round(seg.start, 2), "end": round(seg.end, 2), "text": seg.text.strip(), "words": words,
        })
        print(f"  [{fmt_time(seg.start)}] {seg.text.strip()}")
    out_json.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return data


def loudness_map(audio_wav: Path, window: float = 0.5) -> list[dict]:
    """RMS level per window plus a z-score, so screaming/hype spikes stand out."""
    with wave.open(str(audio_wav), "rb") as wf:
        rate = wf.getframerate()
        raw = wf.readframes(wf.getnframes())
    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    hop = max(1, int(rate * window))
    n = len(samples) // hop
    if n == 0:
        return []
    frames = samples[: n * hop].reshape(n, hop)
    rms = np.sqrt((frames ** 2).mean(axis=1) + 1e-12)
    db = 20 * np.log10(rms + 1e-9)
    z = (db - db.mean()) / (db.std() + 1e-6)
    return [{"t": round(i * window, 2), "db": round(float(db[i]), 1), "z": round(float(z[i]), 2)} for i in range(n)]


def fmt_time(seconds: float) -> str:
    seconds = max(0.0, float(seconds))
    h = int(seconds // 3600)
    m = int(seconds % 3600 // 60)
    s = seconds % 60
    return f"{h}:{m:02d}:{s:04.1f}" if h else f"{m:02d}:{s:04.1f}"


def build_digest(transcript: dict, loud: list[dict], out_txt: Path, title: str = "") -> None:
    """A compact, timestamped transcript for Claude to read and pick moments from.

    Each line: [start-end] text   {LOUD z=2.4}  when the audio peaks inside that segment.
    """
    lines = [
        f"# Digest for: {title}",
        f"# Duration: {fmt_time(transcript.get('duration') or 0)}",
        "# Format: [start - end] (seconds in brackets) text   {LOUD z=..} = audio spike (yelling, hype, laughter)",
        "",
    ]
    peaks = [p for p in loud if p["z"] >= 1.8]
    pi = 0
    for seg in transcript["segments"]:
        while pi < len(peaks) and peaks[pi]["t"] < seg["start"]:
            pi += 1
        z_in = [p["z"] for p in peaks[pi:] if p["t"] <= seg["end"]]
        mark = f"   {{LOUD z={max(z_in):.1f}}}" if z_in else ""
        lines.append(
            f"[{fmt_time(seg['start'])} - {fmt_time(seg['end'])}] ({seg['start']:.1f}-{seg['end']:.1f}) {seg['text']}{mark}"
        )
    # Loud stretches with no speech are often the best reactions; list them too.
    lines += ["", "# Loudest moments (top 40, seconds):"]
    for p in sorted(loud, key=lambda p: p["z"], reverse=True)[:40]:
        lines.append(f"  {p['t']:.1f}s ({fmt_time(p['t'])})  z={p['z']}")
    out_txt.write_text("\n".join(lines), encoding="utf-8")


def prepare(wd: Path, source: Path, profile: dict, title: str = "") -> Path:
    """Audio -> transcript.json + loudness.json + digest.txt inside the work dir."""
    audio = wd / "audio16k.wav"
    if not audio.exists():
        print("Extracting audio...")
        extract_audio(source, audio)
    tjson = wd / "transcript.json"
    if tjson.exists():
        transcript = json.loads(tjson.read_text(encoding="utf-8"))
        print("Transcript already exists, reusing it.")
    else:
        t = profile.get("transcribe", {})
        transcript = transcribe(audio, tjson, t.get("model", "small"), profile.get("language", "en"), t.get("device", "auto"))
    loud = loudness_map(audio)
    (wd / "loudness.json").write_text(json.dumps(loud), encoding="utf-8")
    digest = wd / "digest.txt"
    build_digest(transcript, loud, digest, title)
    return digest


def words_between(transcript: dict, start: float, end: float) -> list[dict]:
    """Words inside [start, end], with times shifted to be relative to `start`."""
    out = []
    for seg in transcript.get("segments", []):
        if seg["end"] < start or seg["start"] > end:
            continue
        for w in seg.get("words", []):
            if w["start"] >= start - 0.05 and w["end"] <= end + 0.3:
                out.append({"start": max(0.0, w["start"] - start), "end": max(0.0, w["end"] - start), "word": w["word"]})
    return out
