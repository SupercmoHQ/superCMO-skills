---
name: example-skill
description: TEMPLATE — demonstrates the standard skill layout and conventions. Replace this line with WHAT the skill does and WHEN to use it, including the trigger phrases a user would say. Delete this skill once real skills are added.
license: Apache-2.0
metadata:
  version: "0.1.0"
  category: example
---

# Example Skill (TEMPLATE — delete once real skills exist)

> Reference layout for authoring a new skill. Copy this folder, rename it, and
> follow `docs/skill-authoring-rules.md`. A skill is **self-contained**: it runs
> standalone with the user's own keys, importing nothing from the repo root.

## Triggers / When to use

- <trigger conditions — mirror the keyword phrases in the `description`>
- Don't use for: <counter-triggers that route to another skill>

## Inputs

- <named inputs and defaults>
- Brand context (optional): read from `${SUPERCMO_BRAND_CONTEXT:-./.supercmo/brand-context.json}`

## Instructions

1. <numbered steps the agent follows>
2. Do non-trivial computation / API calls in a **deterministic script**, not by
   token generation: `python3 scripts/example.py --arg <n>`
3. Read `references/example.md` when <condition> (don't inline long doctrine here).
4. Present results; for anything that changes remote state, preview with
   `--dry-run` first and act only on explicit approval.
5. (Optional, additive) For a quality check, **spawn a subagent that reads
   `agents/reviewer.md` as its prompt — or run those steps inline** if the runtime has no
   subagents. `agents/reviewer.md` is a **bundled role prompt** (no frontmatter, not a
   registered subagent), so the skill stays self-contained and portable.

## Decision rules

- <the non-obvious doctrine that makes the output expert-grade>

## Scripts

| Command | Purpose |
|---|---|
| `python3 scripts/example.py --arg <n>` | <what it does> |
| `python3 scripts/example.py --dry-run` | Print the request that WOULD be sent (no call, secrets masked) |

## References

- `references/example.md` — <when to read it>

## Common pitfalls

1. <mistake → fix>

## Verification checklist

- [ ] <post-run checks>
