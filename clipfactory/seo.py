"""Search metadata for uploads: title checks, tags and hashtags.

Claude writes each clip's title/description/hashtags in plan.json (see docs/SEO.md).
This module only checks them against the channel's `seo:` block and builds the
tag list that goes into the upload notes. YouTube tags are capped at 500 characters.
"""
from __future__ import annotations

TAGS_MAX_CHARS = 500
TITLE_FEED_CHARS = 40  # roughly what the Shorts feed shows before cutting the title
MAX_HASHTAGS = 5


def _names(seo: dict) -> list[str]:
    return [n.lower() for n in [seo.get("keyword", ""), *seo.get("aliases", [])] if n]


def title_warnings(clip: dict, seo: dict) -> list[str]:
    """Warnings for one clip's search metadata (never errors: the team can ignore them)."""
    out = []
    cid = clip.get("id", "?")
    title = (clip.get("title") or "").lower()
    names = _names(seo)
    if names:
        hits = [title.find(n) for n in names if n in title]
        if not hits:
            out.append(f"{cid}: title does not name the creator ({seo.get('keyword')}); searchers type the name")
        elif min(hits) > TITLE_FEED_CHARS:
            out.append(f"{cid}: creator name is past the first {TITLE_FEED_CHARS} characters; move it forward")
    tags = clip.get("hashtags", [])
    if len(tags) > MAX_HASHTAGS:
        out.append(f"{cid}: {len(tags)} hashtags; use 3-{MAX_HASHTAGS} (more looks spammy, 60+ are all ignored)")
    if not (clip.get("description") or "").strip():
        out.append(f"{cid}: no description; first line should say who/what/where in plain words")
    return out


def build_tags(clip: dict, seo: dict) -> list[str]:
    """Clip tags first, then the channel's evergreen tags; deduped, within YouTube's 500 characters."""
    seen, out, used = set(), [], 0
    for tag in [*clip.get("tags", []), *seo.get("tags", [])]:
        tag = str(tag).strip().lstrip("#")
        key = tag.lower()
        if not tag or key in seen:
            continue
        cost = len(tag) + (2 if " " in tag else 0) + (1 if out else 0)  # quotes for spaces, comma between
        if used + cost > TAGS_MAX_CHARS:
            break
        seen.add(key)
        out.append(tag)
        used += cost
    return out


def hashtags(clip: dict, seo: dict) -> list[str]:
    return clip.get("hashtags") or seo.get("hashtags", [])
