#!/usr/bin/env python3
"""Guard: the provider-key catalog has ONE source of truth — each provider module's BYOK_ENV
(scripts/supercmo_skills/providers/*.py, enumerated by client.provider_modules()). Every non-Python
copy of the key list must stay in lockstep, or a new provider's key silently goes missing from a
distribution channel (exactly how WAVESPEED_API_KEY was absent from server.json + mcpb):

  - bin/lib/config.js   ensureKeyFile()          — the `~/.supercmo/.env` placeholders a user fills in
  - server.json         environmentVariables     — the MCP-registry listing metadata
  - mcpb/manifest.json  server.mcp_config.env    — the Claude Desktop / Smithery bundle bindings

SUPERCMO_API_KEY (managed lane) is not a BYOK provider and is intentionally absent from all three,
so it's excluded. Run in CI (validate.yml). Blocking.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

from supercmo_skills import client  # noqa: E402


def registry_keys():
    return {mod.BYOK_ENV for mod in client.provider_modules().values()}


def env_template_keys():
    # ponytail: the ensureKeyFile() .env body writes one placeholder per provider as a quoted dotenv
    # line, e.g. 'FAL_KEY='. That `'KEY='` shape is unique to the template in config.js, so a
    # whole-file scan is unambiguous and dependency-free. If another `'KEY='` literal is ever added
    # elsewhere in config.js, scope this to the ensureKeyFile() body instead.
    src = open(os.path.join(ROOT, "bin", "lib", "config.js"), encoding="utf-8").read()
    keys = set(re.findall(r"""['"]([A-Z][A-Z0-9_]*)=['"]""", src))
    if not keys:
        print("✗ check_catalog_sync: no 'KEY=' placeholders found in bin/lib/config.js ensureKeyFile()")
        raise SystemExit(1)
    return keys


def server_json_keys():
    """Provider keys advertised in server.json (the MCP-registry listing metadata)."""
    with open(os.path.join(ROOT, "server.json"), encoding="utf-8") as f:
        data = json.load(f)
    return {e["name"] for e in data["packages"][0]["environmentVariables"]}


def mcpb_keys():
    """Provider keys the .mcpb bundle binds (Claude Desktop / Smithery UI)."""
    with open(os.path.join(ROOT, "mcpb", "manifest.json"), encoding="utf-8") as f:
        data = json.load(f)
    return set(data["server"]["mcp_config"]["env"].keys())


def main():
    reg = registry_keys()
    # Each surface that carries a copy of the BYOK key list, and its extractor.
    surfaces = [
        ("bin/lib/config.js ensureKeyFile()", env_template_keys),
        ("server.json environmentVariables", server_json_keys),
        ("mcpb/manifest.json server.mcp_config.env", mcpb_keys),
    ]
    drift = [(name, got) for name, fn in surfaces for got in (fn(),) if got != reg]
    if drift:
        print("✗ provider-key catalog drift vs the provider registry:")
        for name, got in drift:
            print(f"  - {name}: {sorted(got)} != registry {sorted(reg)} "
                  f"(missing {sorted(reg - got)}, extra {sorted(got - reg)})")
        return 1
    print(f"✓ provider-key catalog in sync ({len(reg)} keys): registry == .env template + server.json + mcpb")
    return 0


if __name__ == "__main__":
    sys.exit(main())
