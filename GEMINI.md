# SuperCMO Skills — Gemini CLI Guide

Open, **bring-your-own-keys** marketing skills. The same `skills/*/SKILL.md` set used by every other
host works here unchanged. Nothing routes through SuperCMO — every skill runs on the user's own keys.

## Tools

- **Skills** (`skills/*/SKILL.md`): `generating-images`, `video-generation`, `tts-generation`,
  `product-photoshoot`, `supercmo-setup`.
- **Media MCP server** (`.mcp.json` → `mcp-server/server.py`): `image_generate`, `video_generate`,
  `text_to_speech`, and the `list_*_models` helpers. Add it to your Gemini CLI MCP settings; it reads
  BYO keys from the environment.

## Bring your own keys

Put one key in your host's MCP config `env` block (or export it in your shell) — `FAL_KEY` alone
covers image, video, and tts. The server reads keys from its process environment (the MCP standard
for stdio servers). Run `python3 scripts/doctor.py` to confirm what's configured, or the
**supercmo-setup** skill for a guided walkthrough.

## Notes

- Generated media is saved locally; the absolute path is returned in `path` (dir via `output_dir` or
  `$SUPERCMO_OUTPUT_DIR`, default `./supercmo-media`).
- Always `dry_run` first to preview the request + cost before spending.
