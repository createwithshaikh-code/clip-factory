# Instructions for coding agents (OpenAI Codex CLI and others)

Read and follow `CLAUDE.md`: it describes the whole pipeline, the plan format and the rules.
The same steps work from Codex: run the `python -m clipfactory ...` commands, read `work/<id>/digest.txt`,
write `work/<id>/plan.json`, then render. Voice: ElevenLabs MCP if configured, otherwise set
`commentary.engine` to `file` or `system` in the channel YAML.
The channel-manager role for ChatGPT is described in `docs/CHATGPT_AGENT.md`.
