# SuperCMO Skills

Open, model-agnostic, **bring-your-own-keys** marketing skills for AI agents — usable in
Claude Code, Codex, Gemini CLI, Cursor, OpenCode, and other SKILL.md hosts, or installed as one
Claude Code plugin.

Each skill is **self-contained** and runs with *your own keys*. The hosted SuperCMO product
uses these same skills, but that is additive — nothing here depends on it.

**Status:** a working media-generation suite — `generating-images`, `video-generation`,
`tts-generation`, and `product-photoshoot` skills plus the `supercmo` MCP server, all
bring-your-own-keys. `supercmo-setup` onboards new users. Marketing-execution skills (ads, SEO,
social) are in active development. `skills/example-skill/` is the authoring template to copy.

## Install

**As a Claude Code plugin** (the whole repo installs as one plugin):

```
/plugin marketplace add SupercmoHQ/superCMO-skills
/plugin install supercmo@superCMO-skills
```

**As a standalone skill** (any agent): copy a `skills/<name>/` folder into your agent's
skills directory (e.g. `~/.claude/skills/` or a project `.claude/skills/`). Each skill
works on its own.

## Bring your own keys

Set one key in your host's MCP config `env` block (Claude `.mcp.json`, Cursor `.cursor/mcp.json`,
Codex `~/.codex/config.toml`) or export it in your shell — `FAL_KEY` alone covers image + video +
tts. Run `python3 scripts/doctor.py` to see what's configured, or the **supercmo-setup** skill for a
guided walkthrough. Skills read credentials from the process environment (the `SERVICE_API_KEY`
convention, the MCP standard for stdio servers) — never
from a file in the repo. Scripts that change remote state support `--dry-run` (preview the request,
secrets masked) and default to paused/inactive. A hosted metered proxy is an optional fallback
(managed `SUPERCMO_API_KEY` — buy credits + mint a key at getsupercmo.ai/settings?tab=keys); with
your own keys you never touch it.

## Layout

```
.claude-plugin/                 plugin.json + marketplace.json + supercmo.json (product metadata)
.mcp.json                       the supercmo MCP server (image/video/tts tools)
skills/<name>/                  self-contained skills: SKILL.md + references/ + scripts/ + evals/
agents/                         subagents + the OpenCode router entrypoint
commands/                       slash commands (e.g. /supercmo-setup)
mcp-server/                     the media MCP server (thin bindings over scripts/supercmo_skills)
scripts/                        framework: validation, the BYO-keys client, doctor, packaging
AGENTS.md · GEMINI.md · .cursor/rules   per-host entry files (one SKILL.md set, thin wiring)
tests/                          eval harness
docs/                           skill-authoring-rules.md · mcp-authoring-contract.md
```

## Authoring a skill

Full guide: [`CONTRIBUTING.md`](CONTRIBUTING.md). Quick version:

1. Copy `skills/example-skill/` → `skills/<your-skill>/`, rename it (folder name must equal
   the `name` in frontmatter), and follow `docs/skill-authoring-rules.md`.
2. Keep `SKILL.md` short; push detail into `references/`, deterministic work into `scripts/`
   (stdlib-only where possible, BYO-keys from env, `--dry-run` on anything that mutates).
3. Add `evals/eval_cases.json` (should-trigger / should-not-trigger cases).
4. Validate:

```
python3 scripts/quick_validate.py        # structural + frontmatter lint (blocking)
python3 scripts/listing_gate.py          # scripts compile + spend/social --dry-run (blocking)
python3 scripts/check_shared_client.py    # no raw vendor HTTP — the brokering seam (blocking)
python3 tests/evals/run_eval.py           # advisory trigger evals
```

CI runs the same on every push/PR (`.github/workflows/validate.yml`).

## License

Apache-2.0 — see [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).
