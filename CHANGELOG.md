# Changelog

All notable changes to this project are documented here, following
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and
[Semantic Versioning](https://semver.org/).

## [Unreleased]

## [0.1.5] - 2026-07-02

### Changed

- **Credentials now come only from the process environment — the MCP standard for stdio servers**
  ("retrieve credentials from the environment", MCP Authorization spec). Removed the bespoke
  `~/.supercmo/.env` (and plugin-root / cwd `.env`) autoloader (`load_env` / `_parse_env_file`) from
  `supercmo_env`; the MCP server no longer loads any file — it reads keys the host injects.
- Restored a standard `env` block in `.mcp.json` using empty-default expansion
  (`"FAL_KEY": "${FAL_KEY:-}"`, …) — the Claude Code-documented way to pass shell/host values through
  without failing to parse when a var is unset. Other hosts use their own config `env` block
  (Cursor `.cursor/mcp.json`, Codex `~/.codex/config.toml` `[mcp_servers.*.env]`).
- Onboarding (`supercmo-setup`), `doctor.py`, README, AGENTS.md, GEMINI.md, `.cursor/rules`, and the
  MCP-authoring contract now document the host `env` block / shell export as the only key location.
- `mcp-server` server version reported in `initialize` bumped to match the plugin.

### Fixed

- `gemini-tts` now saves a playable file. Gemini TTS returns raw L16 PCM
  (`audio/L16;codec=pcm;rate=24000`); the client had written those bytes to an `.mp3` (the
  content-type fell through to the tts default), producing an unplayable `data` file. The gemini
  provider now wraps the PCM in a WAV container (stdlib `wave`) and returns `audio/wav`, which the
  client maps to `.wav`. Lossless, no new dependency. Verified live: a real `gemini-tts` call saves
  a valid RIFF/WAVE (16-bit mono 24 kHz) file.
- `video_generate` now accepts local file paths for `image_url` / `reference_images`. They were
  passed to the provider raw (unlike `image_generate`, which resolves them via `_encode_refs`), so
  fal tried to HTTP-download a local path → `422 file_download_error`. Video now runs both through
  `_encode_refs` (local path → data-URI; URLs pass through), matching the image path. Verified live:
  `veo3.1-fast` image-to-video from a local PNG returns a saved `.mp4`.

## [0.1.4] - 2026-07-01

### Fixed

- `veo3.1-fast` video generation now works with the default aspect. The veo route mapped
  `square → "1:1"`, but fal's veo3.1 endpoint accepts only `auto` / `16:9` / `9:16` and 422s on
  `1:1`. Mapped `square → "auto"` so a default-aspect call succeeds. Verified live: a real
  image-to-video call returned a saved `.mp4`. (veo3.1-fast is fal's image-to-video model — it
  needs a start frame via `image_url`; pure text-to-video is not offered by this model.)

## [0.1.3] - 2026-07-01

### Fixed

- Media results no longer return the raw inline base64 once the file is saved. `_persist_media`
  drops the `b64` field after writing to disk and returns the local `path` instead. A single tts
  call was returning ~540 KB of base64 inline, overflowing the agent's tool-result token limit;
  the saved file + path carry the same content compactly.

## [0.1.2] - 2026-07-01

### Fixed

- Removed the `env` block from `.mcp.json`. It declared every vendor key as a `${VAR}` template,
  so Claude Code reported "Missing environment variables" (and injected empty keys) whenever a user
  hadn't exported all of them. The MCP server already loads keys from `~/.supercmo/.env` via
  `load_env()` and inherits any exported shell vars, so the injected env block was unnecessary and
  caused a misleading config error on a clean install.

## [0.1.1] - 2026-06-30

### Fixed

- `load_env` now treats an **empty** environment variable as absent and fills it from
  `~/.supercmo/.env`. Previously `setdefault` let an empty `${KEY}` expansion — e.g. a host
  MCP `env` block referencing an unset shell var — shadow the real key, causing "API key not
  valid" even when the key was correctly placed in `~/.supercmo/.env`. A non-empty exported
  value still takes precedence (explicit shell export wins).

## [0.1.0] - 2026-06-27

### Added

- Initial release of `supercmo_skills` — a stdlib-only media client (image / video /
  tts) with provider-blind routing: first available BYO-direct vendor key → one managed
  SuperCMO key → actionable error. Imported by the MCP server, the OSS Hermes app, and
  the hosted proxy.
- Provider adapters: fal, openai, xai, elevenlabs, gemini; `select_route` /
  `proxy_request` over a single catalog.
- Bundled assets: the `supercmo_media` Hermes plugin + image/video/tts skills, shipped as
  package data so the OSS app can materialize them into `HERMES_HOME`.
- Apache-2.0 licensed.
