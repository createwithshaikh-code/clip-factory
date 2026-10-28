"""The edit plan: the JSON file Claude writes after reading digest.txt.

See docs/PLAN_FORMAT.md for the full description. Times inside a clip
(sfx, zooms, commentary_at) are seconds from the start of that clip.
"""
from __future__ import annotations

import json
from pathlib import Path

MOODS = {"hype", "funny", "sad", "emotional", "chill", "suspense"}
LAYOUTS = {"face", "fit_blur"}


class PlanError(ValueError):
    pass


def load_plan(path: Path) -> dict:
    try:
        plan = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PlanError(f"{path} is not valid JSON: {exc}") from exc
    validate(plan)
    return plan


def validate(plan: dict, min_s: float = 8, max_s: float = 60) -> None:
    errors: list[str] = []
    if not isinstance(plan.get("clips"), list) or not plan["clips"]:
        raise PlanError("plan needs a non-empty 'clips' list")
    ids = set()
    for i, c in enumerate(plan["clips"]):
        where = f"clips[{i}] ({c.get('id', '?')})"
        for key in ("id", "start", "end", "title"):
            if key not in c:
                errors.append(f"{where}: missing '{key}'")
        if "start" in c and "end" in c:
            dur = float(c["end"]) - float(c["start"])
            if not (min_s <= dur <= max_s):
                errors.append(f"{where}: length {dur:.1f}s is outside {min_s}-{max_s}s")
        if c.get("id") in ids:
            errors.append(f"{where}: duplicate id")
        ids.add(c.get("id"))
        if c.get("mood") and c["mood"] not in MOODS:
            errors.append(f"{where}: mood must be one of {sorted(MOODS)}")
        if c.get("layout") and c["layout"] not in LAYOUTS:
            errors.append(f"{where}: layout must be one of {sorted(LAYOUTS)}")
        dur = float(c.get("end", 0)) - float(c.get("start", 0))
        for s in c.get("sfx", []):
            if "t" not in s or "name" not in s:
                errors.append(f"{where}: each sfx needs 't' and 'name'")
            elif not (0 <= float(s["t"]) <= dur):
                errors.append(f"{where}: sfx '{s['name']}' at {s['t']}s is outside the clip")
        for z in c.get("zooms", []):
            if "t" not in z:
                errors.append(f"{where}: each zoom needs 't'")
    if errors:
        raise PlanError("Plan problems:\n  - " + "\n  - ".join(errors))


TEMPLATE = {
    "video_id": "<work folder name>",
    "channel": "<channel slug>",
    "clips": [
        {
            "id": "c01",
            "start": 0.0,
            "end": 30.0,
            "title": "Short YouTube title (<= 70 chars)",
            "hook_text": "TEXT ON SCREEN FOR THE FIRST 3s",
            "mood": "funny",
            "layout": "face",
            "commentary": "One or two sentences of your own context/opinion, spoken at commentary_at.",
            "commentary_at": 0.0,
            "sfx": [{"t": 4.2, "name": "vine_boom"}],
            "zooms": [{"t": 4.2, "scale": 1.3, "dur": 0.8}],
            "description": "Upload description",
            "hashtags": ["#shorts"],
        }
    ],
}
