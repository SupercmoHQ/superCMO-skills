# Contributing to SuperCMO Skills

Thanks for adding a skill, agent, or MCP tool. This repo is one cross-host plugin: a skill you author
runs unchanged in Claude Code, Codex, Gemini CLI, Cursor, OpenCode, and other SKILL.md hosts. Two
rules are non-negotiable: **bring-your-own-keys** (never a key in the repo) and **route all
vendor/network calls through `supercmo_env`** (CI enforces it).

Full conventions: [`docs/skill-authoring-rules.md`](docs/skill-authoring-rules.md). This is the short version.

## Add a skill

1. **Copy the template:** `cp -r skills/example-skill skills/<your-skill>` (folder name must equal the
   `name:` in frontmatter — lowercase, hyphenated, `^[a-z0-9]+(-[a-z0-9]+)*$`).
2. **Frontmatter:** `name`, `description` (state WHAT it does + WHEN to use it, including the trigger
   phrases a user would say), `license: Apache-2.0`, and `metadata:` (`version`, `category`, and
   `writes: spend | social | none`). No top-level `version`, no `platforms`, no angle brackets in
   `name`/`description`.
3. **Keep `SKILL.md` short.** Push doctrine into `references/`, deterministic work into `scripts/`.
4. **Scripts are self-contained + BYOK:** stdlib-only where possible; read keys from the environment;
   **import `supercmo_env` and call `supercmo_env._request` / `_request_raw`** for any network — never
   `requests`/`httpx`/`urllib` directly. Anything that mutates remote state (posts, ad spend) must
   support `--dry-run` (preview the request, secrets masked, no network) and default to paused.
5. **Tag money/social actions:** set `metadata.writes: spend` or `social` so the listing gate requires
   your `--dry-run`.
6. **Add `evals/eval_cases.json`** (schema 2): `trigger_keywords` + should-trigger / should-not-trigger
   `cases`. Copy the shape from `skills/generating-images/evals/`.
7. **Validate before you push** (see below). Land each skill as a *complete* PR — folder + `SKILL.md` +
   `evals/` together. Never commit an empty skill folder (the orphan gate fails).

## Add an agent (subagent)

Agents live in `agents/*.md` (or `skills/<name>/agents/*.md` for a skill-bundled role).

- **Standalone subagent:** frontmatter with `name`, `description` (the trigger/when-to-delegate), and
  optional `tools` / `model` / `skills` (preload). It orchestrates skills via the Skill tool; a
  subagent starts in a fresh context and does not inherit loaded skills.
- **Bundled role prompt:** a plain `agents/reviewer.md` with **no frontmatter** (see
  `skills/example-skill/agents/reviewer.md`) — spawned inline by the skill, or run as steps if the host
  has no subagents. Use this to keep a skill self-contained and portable.
- **Skills vs agents:** prefer a skill (portable across all hosts). Reach for an agent only for
  multi-step orchestration or a distinct reviewer role; agents are more host-specific.

## Add an MCP connector

Follow [`docs/mcp-authoring-contract.md`](docs/mcp-authoring-contract.md). In short: drop a
`optional-mcps/<name>/manifest.yaml` (folder name == `name`) declaring `transport` (stdio/http),
`auth.type` (`api_key` | `oauth` | `none`) with credentials as `${ENV}` templates (never inline),
`tools.default_enabled`, and — critically — a `category:` tag (`spend`/`budget`/`publish`) so
money/publish tools auto-pause for approval. The manifest is validated by
`scripts/check_extensions.py` on every PR (an invalid one is otherwise skipped *silently* by the
catalog loader and would just never appear in `supercmo connect`).

## Add a Hermes plugin

A plugin lives in `hermes-plugins/<name>/` and adds native tools:
- `plugin.yaml` — `name`, `version`, `description`, `kind: backend`.
- `__init__.py` — a `register(ctx)` hook that calls `ctx.register_tool(...)` per tool. Handlers are
  `f(args, **kwargs) -> str` (return a JSON string; never raise). See `hermes-plugins/supercmo_media`.
- `schemas.py` — the tool JSON schemas.

It ships and auto-enables with zero central edits. Any vendor/network call must route through
`supercmo_env` — the seam gate scans `hermes-plugins/` too. Structure is checked by
`scripts/check_extensions.py`.

## Validate (must pass before merge)

```
python3 scripts/quick_validate.py        # skills + agents + plugin manifests lint (blocking)
python3 scripts/listing_gate.py          # scripts compile + spend/social --dry-run (blocking)
python3 scripts/check_shared_client.py    # no raw vendor HTTP — the brokering seam (blocking)
python3 scripts/check_extensions.py       # MCP manifests + plugin structure (blocking; needs pyyaml)
python3 tests/evals/run_eval.py           # trigger evals (advisory)
```

CI runs the same on every push/PR (`.github/workflows/validate.yml`). Secret scanning
(`secret-scan.yml`) runs over full history — never commit a key.
