# SuperCMO Skills — Agent Guide

Open, **bring-your-own-keys** marketing skills for AI agents. One SKILL.md set runs across Claude
Code, Codex, Gemini CLI, Cursor, OpenCode, and other SKILL.md-compatible hosts — no per-host
variants. Nothing routes through SuperCMO; every skill runs on the user's own vendor keys.

## What's here

- **Skills** (`skills/*/SKILL.md`) — auto-discovered on hosts that support the SKILL.md standard:
  `generating-images`, `video-generation`, `tts-generation`, `product-photoshoot`, and
  `supercmo-setup` (onboarding).
- **Media MCP server** (`.mcp.json` → `mcp-server/server.py`) — exposes `image_generate`,
  `video_generate`, `text_to_speech` (+ `list_*_models`). Register it via your host's MCP config;
  it reads BYO keys from the environment (`${FAL_KEY}` etc.).

## Bring your own keys

Set one key (e.g. `FAL_KEY`, which covers image + video + tts) in your host's MCP config `env` block
(Claude `.mcp.json`, Cursor `.cursor/mcp.json`, Codex `~/.codex/config.toml`), or export it in your
shell — the server reads keys from its process environment (the MCP standard for stdio servers).
If a tool returns `no_provider_configured`, run the **supercmo-setup** skill or
`python3 scripts/doctor.py` to see what's set vs missing. Never put a key in a file inside the repo.

## Using the media tools

- Invoke a capability skill; it routes the brief to the right model and structures the prompt.
- Generated media is **saved to a local file** — the absolute path is returned in `path` (directory
  via `output_dir` or `$SUPERCMO_OUTPUT_DIR`, default `./supercmo-media`).
- Preview the request + cost with `dry_run` before any real generation.

## Setup / health

- `python3 scripts/doctor.py` — keys set/missing + which capabilities are ready (`--check` adds a
  free key-validity probe, no paid call).
- New here? Start with the **supercmo-setup** skill.
