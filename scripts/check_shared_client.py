#!/usr/bin/env python3
"""Shared-client seam gate.

Runtime vendor/network calls in the skill + MCP surface MUST route through `supercmo_env`
(`supercmo_env._request` / `_request_raw`), never raw HTTP. This is the seam that keeps
managed/brokered delivery an additive flip later (the client gains a gateway path; every
caller inherits it) instead of a per-server rewrite. `scripts/supercmo_env.py` is the ONE
file allowed to use stdlib urllib — it is not in the scanned dirs.

Fails (exit 1) on any direct import of a low-level HTTP/network module in:
  skills/ · mcp-server/ · scripts/supercmo_skills/
AST-based, so comments/strings never trip it.
"""
import ast
import os
import sys

# Third-party HTTP clients (any submodule counts, e.g. requests.adapters).
THIRD_PARTY = {"requests", "httpx", "aiohttp", "urllib3", "pycurl"}
# Exact stdlib network modules that actually open connections.
BANNED_FULL = {"urllib.request", "http.client", "socket"} | THIRD_PARTY
SCAN_DIRS = ["skills", "mcp-server", os.path.join("scripts", "supercmo_skills")]
# Documented exemptions: files that legitimately do non-vendor egress and are NOT brokered.
# telemetry.py POSTs first-party, anonymous usage events to the public telemetry endpoint — not a
# vendor API call the managed proxy intercepts — so it is out of scope of the vendor-seam rule.
EXEMPT = {os.path.join("scripts", "supercmo_skills", "telemetry.py")}


def _hits(tree):
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in BANNED_FULL or alias.name.split(".")[0] in THIRD_PARTY:
                    out.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod in BANNED_FULL or mod.split(".")[0] in THIRD_PARTY:
                out.append(mod)
            elif mod in ("urllib", "http"):  # `from urllib import request` / `from http import client`
                for alias in node.names:
                    if alias.name in ("request", "client"):
                        out.append(f"{mod}.{alias.name}")
    return out


def main():
    violations = []
    for d in SCAN_DIRS:
        if not os.path.isdir(d):
            continue
        for root, _dirs, files in os.walk(d):
            for fn in files:
                if not fn.endswith(".py"):
                    continue
                path = os.path.join(root, fn)
                if path in EXEMPT:
                    continue
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        tree = ast.parse(f.read(), path)
                except (OSError, SyntaxError) as exc:
                    violations.append((path, f"parse error: {exc}"))
                    continue
                hits = _hits(tree)
                if hits:
                    violations.append((path, "raw network import(s): " + ", ".join(sorted(set(hits)))))

    if violations:
        print("❌ Shared-client seam gate FAILED — vendor/network calls must route through supercmo_env:")
        for path, why in violations:
            print(f"   {path}: {why}")
        print("   Fix: `import supercmo_env` and call supercmo_env._request / _request_raw instead of raw HTTP.")
        return 1
    print("✓ Shared-client seam gate PASSED (no raw HTTP in skills/, mcp-server/, "
          "supercmo_skills/).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
