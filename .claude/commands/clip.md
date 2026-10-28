---
description: Make clips from one video for one channel. Usage /clip <channel> <video URL or file> [number of clips]
argument-hint: <channel> <url-or-file> [number of clips]
---
Make Shorts from one source video. Arguments: $ARGUMENTS (first word = channel slug, second = URL or file path, optional third = how many clips to make).

Follow CLAUDE.md. Steps:
1. Read `channels/<channel>.yaml` and `ops/strategy.md` (if it exists).
2. Run `./cf assets` and read `assets/catalog.md` (which SFX and music exist and what they sound like).
3. Run `./cf prepare <url-or-file> --channel <channel>` and note the work folder it prints.
4. Read `work/<id>/digest.txt` in parts. Pick the best moments: the funniest, most hyped, most shocking,
   the biggest "wow" or plot-twist moments. If a number of clips was given, make exactly that many (the strongest ones);
   otherwise as many as the video really has, usually 3-8. Use `./cf frames` when you need to see what is happening.
5. For each chosen moment run `./cf words <id> <start> <end>` and place SFX on the exact words (CLAUDE.md, "SFX, music, zooms").
6. Write `work/<id>/plan.json` (docs/PLAN_FORMAT.md) with hook_text, commentary in the channel persona, mood, SFX that exist in `assets/sfx/`, and zooms.
7. Run `./cf validate work/<id>/plan.json` and fix any errors.
8. If the channel's `commentary.engine` is `elevenlabs`, make each clip's voice with the ElevenLabs MCP (docs/ELEVENLABS.md) and save it as `work/<id>/voice/<clip_id>.mp3`.
9. Run `./cf render work/<id>/plan.json`.
10. Look at a frame or two of the results, then report: each clip's file, title, start-end, why you picked it, and which SFX/music you used where and why.
