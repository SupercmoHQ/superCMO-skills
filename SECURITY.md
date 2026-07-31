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

Skills in this repository contain **instructions and executable code**. The skills
here generate media on your own API keys — which **costs money per call** — and read
public product pages. Treat installing a skill like installing software:

- **Review before use.** Read `SKILL.md`, `scripts/`, and any bundled files
  before running a skill, especially ones that make network calls.
- **Bring your own keys.** Credentials are read from your own environment
  variables and never stored in this repo. Never commit a credential.
- **Preview before you spend.** Generation tools support `dry_run` — it shows the
  exact request and cost with no API call. Inspect the preview before approving a
  paid call.
- **Report misbehavior.** If a skill takes actions that don't match its stated
  purpose, report it via the process above.
