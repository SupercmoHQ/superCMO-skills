# Telemetry

SuperCMO collects **anonymous, opt-out** usage telemetry so we can see which tools people
actually use and prioritise development. It is measured in **one format across every
surface** — the MCP server and direct library use — at the shared client dispatch every
call funnels through. **This page is our telemetry privacy statement** — the complete,
authoritative list of what is and isn't collected, and how long we keep it. If anything
here is unclear, please open an issue.

## What we collect

For each tool invocation, one event with **only** these fields:

| Field | Example | Why |
| --- | --- | --- |
| `event` | `oss_tool_used` | the event name — a fixed constant, identical on every event |
| `tool_name` | `image_generate` | which tool was used (the whole point) |
| `ok` | `true` | did it succeed |
| `duration_ms` | `1840` | performance |
| `error_class` | `TimeoutError` | exception *type* only — never the message |
| `error_code` | `provider_error` | normalized failure reason (fixed vocabulary) — never raw error text |
| `surface` | `mcp` \| `direct` | which surface the call came from |
| `route` | `byok` \| `proxy` | your own key vs the managed proxy |
| `provider` | `fal` \| `gemini` \| … | which vendor served it (BYOK only) |
| `model_id` | `nano-banana` | which model (a slug, not content) |
| `supercmo_version`, `os`, `arch`, `python_version` | `0.1.6`, `darwin`, `arm64`, `3.11` | compatibility |
| `is_ci`, `agent` | `false`, `claude` | segment CI/agent-driven runs |
| `install_id` | `a1b2…` (random UUID4) | approximate unique installs + retention |
| `session_id`, `event_id`, `sample_rate` | — | ordering / dedupe |

## What we NEVER collect

- Your **prompts** or any **tool arguments** (image/video prompts are user content).
- **Generated** images, videos, audio, or their URLs.
- **File paths, file names, or file contents.**
- **API keys** of any kind.
- Your **hostname, username, MAC address, or machine fingerprint.**
- Your **IP address** — it is used only transiently for rate-limiting at ingest and is
  never stored.
- Any **account identity.** The random install id is **never** linked to a SuperCMO
  account, even for managed-key users.

The client sends **only the allowlist above** — the field list is an allowlist in code
(`scripts/supercmo_skills/telemetry.py`), so nothing else can leak by accident.

## The install id

A random UUID4 generated once and stored at `~/.local/state/supercmo/install-id`
(`%LOCALAPPDATA%\supercmo` on Windows). It is **not** derived from any machine attribute.
Delete that file to rotate it. In CI it is not persisted; all CI runs share the single id
`"CI"`.

## How to turn it off

Any one of these disables telemetry completely (env vars win over everything):

- `SUPERCMO_TELEMETRY=false`
- `DO_NOT_TRACK=1` (the [Do Not Track](https://consoledonottrack.com/) standard)
- `DISABLE_TELEMETRY=1`
- `CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC` (inherited from Claude Code)

To **see** what would be sent without sending it: `SUPERCMO_TELEMETRY=log` prints each
payload to stderr.

## Where it goes & how long we keep it

Events are POSTed to our own first-party endpoint, `https://api.getsupercmo.ai/api/v1/telemetry/events`
— never to a third-party analytics host directly. Server-side we forward anonymised events
to PostHog (our analytics processor). Firewall that endpoint to block telemetry at the
network layer if you prefer.

**Retention:** we keep events only for PostHog's default data-retention window — currently 1 year on
PostHog's free plan, up to 7 years on paid plans — after which PostHog deletes them. We do not extend
it. Since everything here is anonymous (no account, no IP, no machine identity), there is nothing to
tie a retained event back to you.

## How it's delivered (why it can't slow you down)

Each event is appended to a small local spool file; a background thread uploads batches
best-effort with a short timeout and gives up silently on failure. A telemetry problem can
never block, delay, or break a tool call — it fails closed and stays out of your way.
