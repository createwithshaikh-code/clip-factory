# clip-factory: instructions for Claude Code

This repo turns long streams and videos into vertical Shorts (30-45 s) for many channels.
You (Claude Code) do the thinking parts: research, choosing moments, writing commentary,
making the voice with the ElevenLabs MCP, and running the render. Python does the editing.
There is no paid LLM API anywhere: the moment picking is done by you, inside this session.

Uploading is done by the team (or their ChatGPT agent). Never upload anything yourself.

## The pipeline

```
discover  ->  prepare  ->  (you) plan.json  ->  (you) voice files  ->  render  ->  output/<channel>/
```

| step | command | what it makes |
|---|---|---|
| research | `python -m clipfactory discover <channel>` | `research/<channel>/videos.md`: the creator's newest videos with views, plus already-viral clips of them |
| prepare | `python -m clipfactory prepare <url or file> --channel <channel>` | `work/<id>/source.mp4`, `transcript.json`, `digest.txt`, `plan.template.json` |
| plan | you write `work/<id>/plan.json` | the edit plan (format: `docs/PLAN_FORMAT.md`) |
| check | `python -m clipfactory validate work/<id>/plan.json` | errors to fix |
| voice | ElevenLabs MCP `text_to_speech` | `work/<id>/voice/<clip_id>.mp3` (see `docs/ELEVENLABS.md`) |
| render | `python -m clipfactory render work/<id>/plan.json` | `output/<channel>/<date>_<id>_<clip>.mp4` + `.txt` with title/description, refreshes `ops/queue.csv` |

Run every command from the repo root through the shortcut, which uses the project's `.venv`:
`./cf <command>` (macOS, and Git Bash on Windows, which is what Claude Code uses there) or `cf <command>`
(Windows cmd/PowerShell). So `python -m clipfactory render ...` above means `./cf render ...`.
If something is missing, run `./cf check`. Setup: `scripts/setup_mac.sh` or `scripts/setup_windows.ps1`.

## Before you start any channel's work

1. Read `channels/<channel>.yaml` (niche, persona, sources, searches, posts_per_day).
2. Read `ops/strategy.md` if it exists. The ChatGPT channel-manager writes it: trends, what performed,
   what to avoid, posting times. Follow it.
3. Read `ops/sources_used.csv` so you never clip the same long video twice for the same channel.

## Picking moments (the most important part)

Read `work/<id>/digest.txt` in parts (it can be long). Each line has the time in seconds in brackets
and `{LOUD z=..}` when the audio spikes (yelling, laughing, hype). At the bottom is a list of the loudest moments.
You can also web-search "<creator> <event>" to learn what people found viral about this stream.

A good clip:
- **Hooks in the first 1-2 seconds.** Start right before the action or the line that makes people stop scrolling, never on small talk.
- **Stands alone.** A viewer who never saw the stream understands it. If not, the commentary gives the missing context.
- **Ends on the payoff** (the punchline, the reaction, the reveal). Cut 0.5-1 s after it; no dead air.
- **Fits the channel length** (`clip.min_seconds`-`clip.max_seconds`, usually 20-45 s, aim for ~30).
- **Is different from the others.** Different moments, different hooks. Never make near-identical clips.

Avoid: sexual content involving anyone who could be a minor, slurs as the punchline, doxxing, real violence,
and long stretches of copyrighted music or TV/sports broadcast footage (these get claims or strikes).

## Commentary (this is what makes the channel monetisable)

YouTube does not pay for clips with "little or no narrative" even with music, SFX and captions. Each clip needs
real added value. For every clip write `commentary`: 1-2 short spoken sentences (max ~7 s) in the channel's
`commentary.persona`, in US English, that add context or an opinion the original does not have:
- backstory: "This is the stream where Kai's cameraman finally had enough."
- why it matters / what happens next: "Wait for Speed's face when he realises who it is."
- a take: "Druski didn't even blink. This is why the skits work."

Do not narrate what the viewer can see. Do not reuse the same sentence across clips. Put the commentary at
`commentary_at: 0` (intro) or at a natural pause (look for gaps between digest lines).

## SFX, music, zooms

- Sound effects: only names that exist in `assets/sfx/` (run `python -m clipfactory check` to see the count, or list the folder).
  Put them right after a punchline or reaction, 1-4 per clip, never on top of the key line. Vary them between clips.
- `mood` picks the music folder: hype, funny, sad, emotional, chill, suspense.
- `zooms`: punch in (scale 1.2-1.45, dur 0.6-1.5) on the reaction face or the key line. Speaker changes and SFX already get small automatic punches.
- `layout`: `face` follows the face (talking, IRL, podcasts). `fit_blur` shows the whole frame (gameplay, wide shots, DIY).

## Daily routine (`/daily <channel>`)

`.claude/commands/daily.md` describes it: read strategy -> discover -> choose source videos not used yet ->
prepare -> plan `posts_per_day` clips (make 1-2 spare) -> voice -> render -> append the plan to
`ops/calendar/<channel>.md` with suggested posting times from `ops/strategy.md`.

## Rules

- Keep times in plan.json in seconds. Times inside a clip (sfx, zooms, commentary_at) are relative to the clip start.
- After rendering, open 1-2 frames (`ffmpeg -ss 2 -i <mp4> -frames:v 1 frame.png`) and look at them if you can.
- Never commit `work/`, `output/`, music files, `.env` or API keys. They are git-ignored.
- Code style: small modules in `clipfactory/`, pathlib everywhere, no OS-specific paths (Windows and macOS must both work).
