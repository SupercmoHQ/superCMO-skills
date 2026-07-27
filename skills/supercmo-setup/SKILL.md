---
name: supercmo-setup
description: Onboards a new SuperCMO user by setting up their bring-your-own API keys and verifying what works. Use when the user says "set up supercmo", "configure my keys", "getting started", "which keys do I need", "connect my keys", or runs the /supercmo-setup command, or when a skill failed with "no_provider_configured". Walks them through adding a vendor key, where it goes for their host, and confirms readiness with the doctor check.
license: Apache-2.0
metadata:
  version: "0.1.0"
  category: onboarding
  writes: none
---

# SuperCMO Setup

Get a new user from zero to a working media skill on **their own keys** (BYOK). No SuperCMO
account or hosted product is required — every skill runs on the user's vendor keys.

## Triggers / When to use

- "set up supercmo", "configure keys", "getting started", "which keys do I need", "/supercmo-setup".
- A skill returned `error: "no_provider_configured"` — the user needs to add a key.
- Don't use for: generating media (that's the image/video/tts skills) — this only sets up keys.

## Instructions

1. **Run the doctor first** to see what's already configured:
   `python3 scripts/doctor.py`
   It lists each vendor key (set vs missing), what each enables, and which capabilities are ready.

2. **Recommend one key to start.** `FAL_KEY` (from fal.ai) is the broadest — it covers
   **image + video + tts** on a single key. Suggest it unless the user already prefers a vendor:
   - `FAL_KEY` — fal.ai — image · video · tts (best starter)
   - `OPENAI_API_KEY` — platform.openai.com — image (gpt-image) · tts
   - `GEMINI_API_KEY` — aistudio.google.com — tts · image analysis (vision)
   - `XAI_API_KEY` — x.ai — image · video
   - `ELEVENLABS_API_KEY` — elevenlabs.io — expressive tts voices
   - `FIRECRAWL_API_KEY` — firecrawl.dev — url extraction (product / web pages)

3. **Tell them where the key goes — the MCP standard is your host's config `env` block** (the
   server reads keys from its process environment). Pick by host:
   - **Claude Code:** the plugin ships an `.mcp.json` that passes these keys through from your
     environment (`"FAL_KEY": "${FAL_KEY:-}"`, etc.). So either `export FAL_KEY=...` in the shell
     that launches Claude, or run `claude mcp add --env FAL_KEY=your-key ...`. To hardcode, set the
     key under the server's `env` in `.mcp.json`.
   - **Cursor:** add it under the server's `env` in `.cursor/mcp.json`:
     `"env": { "FAL_KEY": "your-key" }`.
   - **Codex:** add it to `~/.codex/config.toml` under `[mcp_servers.supercmo.env]`:
     `FAL_KEY = "your-key"`.
   - **Any host / quick test:** `export FAL_KEY=...` in the shell before launching the host — the
     server reads it from the process environment.
   - Never paste a key into a file inside the repo; it lives in your host's MCP config `env` block
     or your shell environment.

4. **Verify** — re-run the doctor; for a live key-validity probe (free, no generation):
   `python3 scripts/doctor.py --check`
   Confirm the target capability shows ✓ ready.

5. **Try it** — suggest a first generation, always previewing with `dry_run` first when the user
   wants to see the request/cost before spending. Example: ask the image skill for a simple test image.

## Decision rules

- One key is enough to start; don't ask the user to configure them all. Default to `FAL_KEY`.
- If the user is privacy-conscious or offline-first, reassure them: keys stay in their environment,
  calls go directly to the vendor, nothing routes through SuperCMO.
- BYOK is the default and needs no account. A managed `SUPERCMO_API_KEY` is an optional alternative — buy credits + mint a key at `getsupercmo.ai/settings?tab=keys` — one key covers every media model without your own vendor keys.

## Scripts

| Command                             | Purpose                                                        |
| ----------------------------------- | -------------------------------------------------------------- |
| `python3 scripts/doctor.py`         | List keys (set/missing), what each enables, capabilities ready |
| `python3 scripts/doctor.py --check` | Same, plus a free key-validity probe (no paid call)            |

## Common pitfalls

1. Key exported but the MCP server can't see it → it was exported _after_ the host started, or the
   host was launched from a GUI with no shell environment. Fix: put it in the host's MCP config
   `env` block, or export it and restart the host so the server subprocess inherits it.
2. `no_provider_configured` after adding a key → wrong variable name; match the exact name above.

## Verification checklist

- [ ] `python3 scripts/doctor.py` shows at least one vendor key `set` and the target capability ✓.
- [ ] A `dry_run` generation returns a request preview (no spend); a real run returns a saved local path.
