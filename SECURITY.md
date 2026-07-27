# Security Policy

## Reporting a vulnerability

**Do not open a public issue for security problems.** Email
**founder@getsupercmo.ai** with:

- a description of the issue and its impact,
- steps to reproduce (or a proof of concept),
- the skill / file / version affected.

We aim to acknowledge within **3 business days** and to provide a remediation
timeline after triage. Please give us a reasonable window to fix the issue
before any public disclosure. We'll credit reporters who want credit.

## Supported versions

Security fixes are applied to the latest released version. Older versions are
not maintained — upgrade to the latest before reporting.

## Skill safety model (read this)

Skills in this repository contain **instructions and executable code**, and can
act on accounts you connect (e.g. ad and social platforms). Treat installing a
skill like installing software:

- **Review before use.** Read `SKILL.md`, `scripts/`, and any bundled files
  before running a skill, especially ones that make network calls or mutate
  remote state.
- **Bring your own keys.** Credentials are read from your own environment
  variables and never stored in this repo. Never commit a credential.
- **Mutations preview first.** Scripts that change remote state support
  `--dry-run` and create remote objects paused/inactive by default. Inspect the
  previewed request before approving a live action.
- **Report misbehavior.** If a skill takes actions that don't match its stated
  purpose, report it via the process above.
