<!-- Thanks for contributing to SuperCMO skills! -->

## What this changes

<!-- Brief description. Link any related issue. -->

## Type

- [ ] New skill
- [ ] Change to an existing skill
- [ ] Shared tool (`tools/`)
- [ ] Docs / repo infrastructure

## Checklist

- [ ] No credentials, tokens, or secrets are committed (keys come from env vars).
- [ ] `name` matches the folder; `description` says **what + when** and is ≤ 1024 chars.
- [ ] Skill passes validation (`skills-ref validate <skill>` and the frontmatter lint).
- [ ] SKILL.md body is under ~500 lines; detail is in `references/`.
- [ ] Any script that mutates remote state supports `--dry-run` and defaults to paused/inactive.
