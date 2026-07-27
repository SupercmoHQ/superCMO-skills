# SuperCMO generation MCP server

A local MCP server bundled with the SuperCMO plugin. It exposes the generation tools that
skills call. Standard-library Python only; starts automatically when the plugin is enabled —
no separate install.

## Available Tools

- `image_generate` - Generate a still image from a text prompt.
  - Required arguments:
    - `prompt` (string): the image description.
  - Optional arguments:
    - `model` (string): a model name; omit for the default (`nano-banana-2`). Call `list_image_models`
      to see the options.
    - `aspect_ratio` (string): `square` (default), `landscape`, `portrait`.
    - `num_images` (integer): how many to generate (default 1, max 4).
    - `seed` (integer): for reproducible results.
    - `dry_run` (boolean): return the request that would be sent (key masked), make no API call.
- `list_image_models` - List available image models (name, strengths, price). Optional
  discovery — use only when choosing a model. Optional `query` filters by use-case keyword.

## Configuration

Declared in the plugin's `.mcp.json` (plugin root); Claude Code starts it automatically when
the plugin is enabled:

```json
{
  "mcpServers": {
    "supercmo": {
      "command": "python3",
      "args": ["${CLAUDE_PLUGIN_ROOT}/mcp-server/server.py"],
      "env": { "SUPERCMO_API_KEY": "${SUPERCMO_API_KEY}", "SUPERCMO_API_URL": "${SUPERCMO_API_URL}", "FAL_KEY": "${FAL_KEY}" }
    }
  }
}
```

Requires `python3` on PATH (no `pip install` — standard library only).

## Keys

Set one key in `~/.claude/settings.json` (or `export` it before launching):

```json
{ "env": { "SUPERCMO_API_KEY": "your-supercmo-key" } }
```

Routing is **BYOK-direct > managed** (resolved in `supercmo_skills`): if a vendor key like
`FAL_KEY` is set, the call goes direct to that vendor; otherwise it routes through the managed
SuperCMO proxy with `SUPERCMO_API_KEY`. With neither set, the tool returns a setup hint. One
`SUPERCMO_API_KEY` covers every media model; `FAL_KEY` is an optional bring-your-own escape
hatch. Get a SuperCMO key at <https://getsupercmo.ai/settings?tab=keys>; a fal key at <https://fal.ai/dashboard/keys>.

## Smoke test (no network)

```bash
printf '%s\n' \
  '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
  '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' \
  '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"image_generate","arguments":{"prompt":"a red bicycle","dry_run":true}}}' \
  | python3 mcp-server/server.py
```

`dry_run: true` returns the request that would be sent (key masked) — no API call.
