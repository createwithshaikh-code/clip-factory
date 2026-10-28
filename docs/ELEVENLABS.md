# Commentary voice with ElevenLabs (through MCP)

Claude Code talks to ElevenLabs through the official MCP server (`elevenlabs-mcp`), configured in
`.mcp.json` at the repo root. ElevenLabs bills its own credits (free tier: 10k credits a month),
separate from your Claude subscription.

## One-time setup on each computer

1. Install `uv` (the setup scripts do this): it provides the `uvx` command that starts the MCP server.
2. Get an API key at https://elevenlabs.io/app/settings/api-keys
3. Set two environment variables (the setup scripts ask for the key and set both):
   - `ELEVENLABS_API_KEY` = your key
   - `ELEVENLABS_MCP_BASE_PATH` = the full path of this repo (so voice files can be saved into `work/`)
4. Open a **new** terminal, `cd` into the repo, run `claude`, and approve the ElevenLabs server when asked.
   `/mcp` inside Claude Code shows whether it is connected.

Never put the key in a file that is committed.

## How Claude uses it

For every clip in `plan.json` that has `commentary`:

1. Call the ElevenLabs `text_to_speech` tool with the commentary text, the channel's `commentary.voice`
   (keep one voice per channel so each channel sounds like its own person), and
   `output_directory` = `work/<video_id>/voice`.
2. Rename the file it creates to `<clip_id>.mp3` (e.g. `work/druski-abc/voice/c01.mp3`).
3. Keep each line under ~7 seconds. Re-generate if it sounds flat.

`render` then finds `voice/<clip_id>.mp3`, ducks the original audio while it plays, and mixes it in.

## Cost-saving tips

- Generate voice only for clips you will actually post.
- Short lines cost fewer credits (1 character is about 1 credit on most plans).
- The ElevenLabs MCP can also make custom sound effects (`text_to_sound_effects`); save them into `assets/sfx/<name>.mp3` and they become usable in plans.

## No ElevenLabs?

Set `commentary.engine` in the channel YAML to:
- `file`: record your own voice as `work/<id>/voice/<clip_id>.mp3`
- `system`: the computer's built-in voice (free, robotic)
- `piper`: a free local neural voice (https://github.com/rhasspy/piper)
