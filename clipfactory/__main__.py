"""clip-factory command line.  Run `python -m clipfactory --help`."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from . import config
from .config import CHANNELS_DIR, OUTPUT_DIR, WORK_DIR, list_channels, load_channel


def _is_url(s: str) -> bool:
    return s.startswith("http://") or s.startswith("https://")


def cmd_check(args) -> int:
    ok = True
    print(f"Python {sys.version.split()[0]}  ({sys.platform})")
    for mod in ("cv2", "numpy", "PIL", "yaml", "yt_dlp", "faster_whisper"):
        try:
            if mod == "faster_whisper":
                from .transcribe import load_whisper

                load_whisper()
            m = __import__(mod)
            print(f"  ok  {mod} {getattr(m, '__version__', '')}")
        except Exception as exc:  # a blocked DLL can raise OSError as well as ImportError
            ok = False
            print(f"  MISSING  {mod}: {type(exc).__name__}: {exc}")
            if "DLL" in str(exc):
                print("           -> install the Visual C++ runtime: winget install Microsoft.VCRedist.2015+.x64")
            else:
                print("           -> pip install -r requirements.txt")
    try:
        import cv2

        if int(cv2.__version__.split(".")[0]) >= 5:
            ok = False
            print("  PROBLEM  opencv 5 has no face model; run: pip install \"opencv-python-headless<5\"")
    except ImportError:
        pass
    try:
        from .ffmpeg import ffmpeg_bin

        print(f"  ok  ffmpeg: {ffmpeg_bin()}")
    except SystemExit as exc:
        ok = False
        print(f"  MISSING  {exc}")
    font = config.resolve_font("")
    print(f"  {'ok' if font else 'MISSING'}  caption font: {font or 'put a .ttf in assets/fonts'}")
    from .audio import available_sfx

    for name in list_channels():
        prof = load_channel(name)
        sfx = available_sfx(prof)
        music_root = Path(prof["music"].get("folder") or config.MUSIC_DIR)
        moods = {d.name: len([p for p in d.rglob('*') if p.suffix.lower() in config.AUDIO_EXTS])
                 for d in music_root.iterdir() if d.is_dir()} if music_root.exists() else {}
        print(f"  channel {name}: {len(sfx)} sfx, music per mood {moods}, voice={prof['commentary']['engine']}")
    return 0 if ok else 1


def cmd_channels(args) -> int:
    for name in list_channels():
        p = load_channel(name)
        print(f"{name:20s} {p.get('niche', '')}")
    return 0


def cmd_new_channel(args) -> int:
    dst = CHANNELS_DIR / f"{args.slug}.yaml"
    if dst.exists():
        raise SystemExit(f"{dst} already exists")
    text = (CHANNELS_DIR / "_template.yaml").read_text(encoding="utf-8").replace("SLUG", args.slug)
    dst.write_text(text, encoding="utf-8")
    print(f"Created {dst}. Edit it, then run: python -m clipfactory discover {args.slug}")
    return 0


def cmd_discover(args) -> int:
    from .discover import discover

    prof = load_channel(args.channel)
    sources = args.source or prof.get("sources", [])
    searches = args.search or prof.get("research_searches", [])
    if not sources and not searches:
        raise SystemExit("Add 'sources' / 'research_searches' to the channel YAML or pass --source/--search")
    discover(args.channel, sources, searches, args.limit)
    return 0


def cmd_prepare(args) -> int:
    from .download import download, ingest_local, read_meta, source_path
    from .transcribe import prepare

    prof = load_channel(args.channel)
    wd = download(args.input, args.channel) if _is_url(args.input) else ingest_local(Path(args.input), args.channel, args.copy)
    meta = read_meta(wd)
    digest = prepare(wd, source_path(wd), prof, meta.get("title") or "")
    from .discover import record_source

    record_source(args.channel, wd.name, meta.get("url") or args.input, meta.get("title") or "")
    from .plan import TEMPLATE

    tpl = json.loads(json.dumps(TEMPLATE))
    tpl["video_id"] = wd.name
    tpl["channel"] = args.channel
    (wd / "plan.template.json").write_text(json.dumps(tpl, indent=2), encoding="utf-8")
    print("\nReady for moment picking:")
    print(f"  digest : {digest}")
    print(f"  write  : {wd / 'plan.json'}  (format: docs/PLAN_FORMAT.md)")
    print(f"  then   : python -m clipfactory render {wd / 'plan.json'}")
    return 0


def cmd_validate(args) -> int:
    from .audio import find_sfx
    from .download import read_meta
    from .plan import load_plan

    path = Path(args.plan)
    plan = load_plan(path)
    channel = plan.get("channel") or read_meta(path.resolve().parent).get("channel")
    warnings = []
    if channel:
        prof = load_channel(channel)
        lo, hi = prof["clip"]["min_seconds"], prof["clip"]["max_seconds"]
        for c in plan["clips"]:
            dur = float(c["end"]) - float(c["start"])
            if not lo <= dur <= hi:
                warnings.append(f"{c['id']}: {dur:.1f}s is outside this channel's {lo}-{hi}s")
            for s in c.get("sfx", []):
                if not find_sfx(s["name"], prof):
                    warnings.append(f"{c['id']}: sfx '{s['name']}' is not in assets/sfx")
            if not (c.get("commentary") or "").strip():
                warnings.append(f"{c['id']}: no commentary (reused-content risk)")
            if len(c.get("title", "")) > 70:
                warnings.append(f"{c['id']}: title longer than 70 characters")
    for w in warnings:
        print(f"  warning: {w}")
    print(f"OK: {len(plan['clips'])} clip(s), {len(warnings)} warning(s)")
    return 0


def cmd_render(args) -> int:
    from .render import render_plan

    render_plan(Path(args.plan), args.only, args.keep_temp)
    from .discover import update_queue

    update_queue()
    return 0


def cmd_status(args) -> int:
    if not WORK_DIR.exists():
        print("No work yet.")
        return 0
    for wd in sorted(p for p in WORK_DIR.iterdir() if p.is_dir()):
        meta = {}
        if (wd / "meta.json").exists():
            meta = json.loads((wd / "meta.json").read_text(encoding="utf-8"))
        state = "digest" if (wd / "digest.txt").exists() else "new"
        if (wd / "plan.json").exists():
            state = "planned"
        rendered = len(list((OUTPUT_DIR / meta.get("channel", "?")).glob(f"*_{wd.name}_*.mp4")))
        if rendered:
            state = f"rendered {rendered}"
        print(f"{wd.name:45s} {meta.get('channel', ''):15s} {state}")
    return 0


def cmd_queue(args) -> int:
    from .discover import update_queue

    update_queue()
    return 0


def cmd_clean(args) -> int:
    wd = WORK_DIR / args.video_id
    for name in ("tmp", "audio16k.wav", "source.mp4"):
        p = wd / name
        if p.is_dir():
            shutil.rmtree(p, ignore_errors=True)
        elif p.exists() and (name != "source.mp4" or args.source):
            p.unlink()
    print(f"Cleaned {wd}")
    return 0


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):  # Windows consoles default to cp1252
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(prog="clipfactory", description="Long videos -> vertical clips with captions, music, SFX and commentary.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("check", help="check that everything is installed").set_defaults(func=cmd_check)
    sub.add_parser("channels", help="list channel profiles").set_defaults(func=cmd_channels)

    p = sub.add_parser("new-channel", help="create channels/<slug>.yaml from the template")
    p.add_argument("slug")
    p.set_defaults(func=cmd_new_channel)

    p = sub.add_parser("discover", help="list a creator's videos and already-viral clips into research/<channel>/")
    p.add_argument("channel")
    p.add_argument("--source", action="append", help="channel/playlist URL (repeatable)")
    p.add_argument("--search", action="append", help="YouTube search, e.g. 'Druski funny moments' (repeatable)")
    p.add_argument("--limit", type=int, default=30)
    p.set_defaults(func=cmd_discover)

    p = sub.add_parser("prepare", help="download/ingest a video, transcribe it, and write digest.txt")
    p.add_argument("input", help="video URL or local file")
    p.add_argument("--channel", required=True)
    p.add_argument("--copy", action="store_true", help="copy a local file into work/ instead of referencing it")
    p.set_defaults(func=cmd_prepare)

    p = sub.add_parser("validate", help="check a plan.json")
    p.add_argument("plan")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("render", help="render every clip in a plan.json")
    p.add_argument("plan")
    p.add_argument("--only", nargs="*", help="clip ids to render")
    p.add_argument("--keep-temp", action="store_true")
    p.set_defaults(func=cmd_render)

    sub.add_parser("status", help="show every video in work/ and how far it got").set_defaults(func=cmd_status)
    sub.add_parser("queue", help="refresh ops/queue.csv (rendered, not yet posted)").set_defaults(func=cmd_queue)

    p = sub.add_parser("clean", help="delete temp files for a video (add --source to delete the download too)")
    p.add_argument("video_id")
    p.add_argument("--source", action="store_true")
    p.set_defaults(func=cmd_clean)

    args = ap.parse_args(argv)
    from .plan import PlanError

    try:
        return args.func(args) or 0
    except PlanError as exc:
        print(exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
