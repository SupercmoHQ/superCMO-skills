<!-- Thanks for contributing to SuperCMO skills! -->

## What this changes

<!-- Brief description. Link any related issue. -->

## Type

- [ ] New skill
- [ ] Change to an existing skill
- [ ] Shared script / MCP tool (`scripts/`, `scripts/supercmo_skills/mcp/`)
- [ ] Docs / repo infrastructure

## Checklist

- [ ] No credentials, tokens, or secrets are committed (keys come from env vars).
- [ ] `name` matches the folder; `description` says **what + when** and is ≤ 1024 chars.
- [ ] Passes local validation — `python3 scripts/quick_validate.py`, `scripts/listing_gate.py`, `scripts/check_shared_client.py` (CI runs the same).
- [ ] SKILL.md body is under ~500 lines; detail is in `references/`.
- [ ] Any script that mutates remote state supports `--dry-run` and defaults to paused/inactive.
