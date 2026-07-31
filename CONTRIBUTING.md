# Contributing to SuperCMO Skills

Thanks for adding a skill, agent, or MCP tool. This repo is one cross-host plugin: a skill you author
runs unchanged in Claude Code, Cursor, Codex, Claude Cowork, and other SKILL.md-compatible hosts. Two
rules are non-negotiable: **bring-your-own-keys** (never a key in the repo) and **route all
vendor/network calls through `supercmo_env`** (CI enforces it).

`skills/generating-images/` is the reference build — match its shape when in doubt.

## Add a skill

1. **Create the folder:** `skills/<your-skill>/` (folder name must equal the `name:` in frontmatter —
   lowercase, hyphenated, `^[a-z0-9]+(-[a-z0-9]+)*$`). `skills/generating-images/` is the reference
   layout to model it on.
2. **Frontmatter:** `name`, `description` (state WHAT it does + WHEN to use it, including the trigger
   phrases a user would say), `license: Apache-2.0`, and `metadata:` (`version`, `category`; add
   `writes: spend | social` **only** for skills that spend money or post — it defaults to `none`, so
   most skills omit it, like the reference skill does). No top-level `version`, no `platforms`, no
   angle brackets in `name`/`description`.
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

The repo ships no subagents — a skill is portable across every host, while a subagent is
host-specific and starts in a fresh context that does not inherit loaded skills. Reach for one only
for genuine multi-step orchestration or a distinct reviewer role.

- **Bundled role prompt (preferred):** a plain `skills/<name>/agents/<role>.md` with **no
  frontmatter** — spawned inline by the skill, or run as steps if the host has no subagents. Keeps
  the skill self-contained and portable.
- **Standalone subagent:** an `agents/<name>.md` at the repo root with frontmatter — `name`,
  `description` (the trigger/when-to-delegate), and optional `tools` / `model` / `skills` (preload).
  Add it to `.claude-plugin/supercmo.json` → `agents`.

## Validate (must pass before merge)

```
python3 scripts/quick_validate.py        # skills + agents + plugin manifests lint (blocking)
python3 scripts/listing_gate.py          # scripts compile + spend/social --dry-run (blocking)
python3 scripts/check_shared_client.py    # no raw vendor HTTP — the brokering seam (blocking)
python3 tests/evals/run_eval.py           # trigger evals (advisory)
```

CI runs the same on every push/PR (`.github/workflows/validate.yml`). Secret scanning
(`secret-scan.yml`) runs over full history — never commit a key.
