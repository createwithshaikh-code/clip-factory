---
description: Make clips from one video for one channel. Usage /clip <channel> <video URL or file>
argument-hint: <channel> <url-or-file>
---
Make Shorts from one source video. Arguments: $ARGUMENTS (first word = channel slug, second = URL or file path).

Follow CLAUDE.md. Steps:
1. Read `channels/<channel>.yaml` and `ops/strategy.md` (if it exists).
2. Run `./cf prepare <url-or-file> --channel <channel>` and note the work folder it prints.
3. Read `work/<id>/digest.txt` in parts. Pick the best moments (as many as the video really has, usually 3-8; quality over quantity).
4. Write `work/<id>/plan.json` (docs/PLAN_FORMAT.md) with hook_text, commentary in the channel persona, mood, SFX that exist in `assets/sfx/`, and zooms.
5. Run `./cf validate work/<id>/plan.json` and fix any errors.
6. If the channel's `commentary.engine` is `elevenlabs`, make each clip's voice with the ElevenLabs MCP (docs/ELEVENLABS.md) and save it as `work/<id>/voice/<clip_id>.mp3`.
7. Run `./cf render work/<id>/plan.json`.
8. Look at a frame or two of the results, then report: each clip's file, title, start-end and why you picked it.
