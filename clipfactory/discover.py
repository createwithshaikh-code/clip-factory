"""Research helpers: list a creator's videos, and see which moments other clippers already went viral with."""
from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

from .config import OUTPUT_DIR, ROOT

RESEARCH_DIR = ROOT / "research"
OPS_DIR = ROOT / "ops"
POSTING_LOG = OPS_DIR / "posting_log.csv"
LOG_FIELDS = ["date", "channel", "file", "title", "posted_at", "url", "views_24h", "views_7d", "notes"]


def _ydl_flat(url: str, limit: int) -> list[dict]:
    import yt_dlp

    opts = {"quiet": True, "extract_flat": "in_playlist", "playlistend": limit, "skip_download": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
    entries = info.get("entries") or []
    out = []
    for e in entries:
        if not e:
            continue
        if e.get("_type") == "playlist" and e.get("entries"):
            out += [x for x in e["entries"] if x]
        else:
            out.append(e)
    return out[:limit]


def _row(e: dict) -> dict:
    vid = e.get("id")
    url = e.get("url") or ""
    if vid and not url.startswith("http"):
        url = f"https://www.youtube.com/watch?v={vid}"
    return {
        "id": vid,
        "title": e.get("title"),
        "url": url,
        "channel": e.get("channel") or e.get("uploader"),
        "duration_min": round((e.get("duration") or 0) / 60, 1),
        "views": e.get("view_count"),
        "uploaded": e.get("upload_date") or e.get("release_timestamp"),
    }


def discover(channel: str, sources: list[str], searches: list[str], limit: int = 30) -> Path:
    """Write research/<channel>/videos.json + videos.md.

    sources  = creator channel/playlist URLs (long streams and videos to clip from)
    searches = YouTube searches like "Druski funny moments" to see what clips already went viral
    """
    out_dir = RESEARCH_DIR / channel
    out_dir.mkdir(parents=True, exist_ok=True)
    result = {"generated": datetime.now().isoformat(timespec="minutes"), "sources": [], "viral_clips": []}
    for src in sources:
        print(f"Listing {src} ...")
        try:
            result["sources"] += [_row(e) for e in _ydl_flat(src, limit)]
        except Exception as exc:
            print(f"  failed: {exc}")
    for q in searches:
        print(f"Searching YouTube: {q} ...")
        try:
            rows = [_row(e) for e in _ydl_flat(f"ytsearch{limit}:{q}", limit)]
            for r in rows:
                r["query"] = q
            result["viral_clips"] += rows
        except Exception as exc:
            print(f"  failed: {exc}")

    (out_dir / "videos.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    def table(rows: list[dict], with_query: bool = False) -> list[str]:
        rows = sorted(rows, key=lambda r: r.get("views") or 0, reverse=True)
        head = "| views | min | title | url |" + (" query |" if with_query else "")
        lines = [head, "|---|---|---|---|" + ("---|" if with_query else "")]
        for r in rows:
            title = (r.get("title") or "").replace("|", "/")
            line = f"| {r.get('views') or ''} | {r.get('duration_min')} | {title} | {r.get('url')} |"
            if with_query:
                line += f" {r.get('query')} |"
            lines.append(line)
        return lines

    md = [f"# Research: {channel}", f"Generated {result['generated']}", "", "## Source videos (to clip from)"]
    md += table(result["sources"])
    md += ["", "## Clips that already went viral (what people like)"]
    md += table(result["viral_clips"], with_query=True)
    (out_dir / "videos.md").write_text("\n".join(md), encoding="utf-8")
    print(f"Wrote {out_dir / 'videos.md'}")
    return out_dir / "videos.md"


def ensure_ops() -> None:
    OPS_DIR.mkdir(exist_ok=True)
    if not POSTING_LOG.exists():
        with open(POSTING_LOG, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(LOG_FIELDS)


def update_queue() -> Path:
    """ops/queue.csv = every rendered clip that is not in posting_log.csv yet."""
    ensure_ops()
    with open(POSTING_LOG, newline="", encoding="utf-8") as f:
        posted = {row["file"] for row in csv.DictReader(f)}
    rows = []
    for mp4 in sorted(OUTPUT_DIR.glob("*/*.mp4")):
        rel = mp4.relative_to(OUTPUT_DIR).as_posix()
        if rel in posted:
            continue
        notes = mp4.with_suffix(".txt")
        title = ""
        if notes.exists():
            lines = notes.read_text(encoding="utf-8").splitlines()
            title = lines[1] if len(lines) > 1 else ""
        rows.append({"channel": mp4.parent.name, "file": rel, "title": title})
    queue = OPS_DIR / "queue.csv"
    with open(queue, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["channel", "file", "title"])
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} clip(s) waiting to be posted -> {queue}")
    return queue


def record_source(channel: str, video_id: str, url: str, title: str) -> None:
    """ops/sources_used.csv: which long videos were already clipped, so nobody does one twice."""
    ensure_ops()
    path = OPS_DIR / "sources_used.csv"
    new = not path.exists()
    with open(path, newline="", encoding="utf-8") as f:
        seen = {(r["channel"], r["video_id"]) for r in csv.DictReader(f)} if not new else set()
    if (channel, video_id) in seen:
        return
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["date", "channel", "video_id", "url", "title"])
        w.writerow([datetime.now().strftime("%Y-%m-%d"), channel, video_id, url, title])
