# SuperCMO marketing MCP catalog (`optional-mcps/`)

Each `<vendor>/manifest.yaml` describes a marketing MCP server a user can add with
`supercmo connect <vendor>`. This is **Hermes's own optional-MCP catalog format** — SuperCMO
points `HERMES_OPTIONAL_MCPS` at this directory (materialized into `~/.supercmo/optional-mcps/`)
and reuses Hermes's `install_entry` / OAuth / token machinery verbatim. We author only the
manifests (data); no connection code.

## Manifest contract (validated by Hermes `_parse_manifest`)

```yaml
manifest_version: 1                 # required (rejected otherwise)
name: <slug>                        # ^[A-Za-z0-9_-]+$
description: "..."                  # required
category: [ads, spend, publish]    # SuperCMO-only: consumed by the approvals gate (B2).
                                    #   Hermes ignores unknown keys, so this is safe.
install:                           # optional — self-hosted stdio servers
  type: git
  url: "https://github.com/.../server"
  ref: "v1.0.0"                    # PIN a tag; never float
  bootstrap: ["uv sync"]
transport:
  type: stdio | http
  command: "uv"                    # stdio
  args: [...]
  url: "https://..."               # http
auth:
  type: oauth | api_key | none
  scopes: [...]                    # oauth
  env: [{name, prompt, secret}]    # api_key — EVERY credential the server needs
tools:
  default_enabled: [...]           # pre-enabled tool names
post_install: |                    # shown after connect
  ...
```

## Two gotchas (handled by `supercmo connect`, not the manifest author)

1. **stdio + api_key:** Hermes strips ambient env from stdio subprocesses (`_build_safe_env`),
   and the catalog installer doesn't emit an `env:` block. `supercmo connect` adds
   `env: {VAR: "${VAR}"}` for each `auth.env` entry so the server actually receives the creds.
2. **OAuth dynamic client registration:** Meta may reject RFC-7591 DCR. If the browser flow
   completes but no token lands, `supercmo connect` prompts for a pre-registered
   `client_id`/`client_secret`.

## Status of the shipped entries

| Vendor | Transport | Auth | Ready? |
|---|---|---|---|
| meta-ads | http | oauth | endpoint TODO — confirm before launch |
| google-ads | stdio (git) | api_key | server repo TODO — pin before launch |
| tiktok-ads | http | oauth | endpoint TODO |
| postiz | http | api_key (bearer) | works with your self-hosted Postiz URL + key |
