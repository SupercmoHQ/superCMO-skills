#!/usr/bin/env python3
"""SuperCMO generation MCP server — JSON-RPC stdio plumbing.

Exposes the generation tools (see tools/) over MCP stdio. See mcp-server/README.md.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))

import registry
import tools  # noqa: F401,E402 (registers tools on import)

SERVER_NAME = "supercmo"
SERVER_VERSION = "0.1.5"
DEFAULT_PROTOCOL = "2025-06-18"


def log(msg):
    print(f"[{SERVER_NAME}] {msg}", file=sys.stderr, flush=True)


def _result(req_id, result):
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def _error(req_id, code, message):
    return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}


def handle(msg):
    """Dispatch one JSON-RPC message. Returns a response dict, or None for notifications."""
    method = msg.get("method")
    req_id = msg.get("id")

    if method == "initialize":
        proto = (msg.get("params") or {}).get("protocolVersion") or DEFAULT_PROTOCOL
        return _result(req_id, {
            "protocolVersion": proto,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        })

    if method in ("notifications/initialized", "initialized"):
        return None

    if method == "ping":
        return _result(req_id, {})

    if method == "tools/list":
        return _result(req_id, {"tools": registry.schemas()})

    if method == "tools/call":
        params = msg.get("params") or {}
        name = params.get("name")
        fn = registry.handler(name)
        if not fn:
            return _error(req_id, -32602, f"Unknown tool: {name}")
        try:
            out = fn(params.get("arguments") or {})
        except Exception as e:
            log(f"tool {name} raised: {type(e).__name__}: {e}")
            out = {"ok": False, "error": f"{type(e).__name__}: {e}"}
        return _result(req_id, {
            "content": [{"type": "text", "text": json.dumps(out, indent=2)}],
            "isError": not out.get("ok", False),
        })

    if req_id is None:
        return None
    return _error(req_id, -32601, f"Method not found: {method}")


def main():
    # Credentials come from the process environment the host injects (MCP stdio standard).
    log("ready (stdio)")
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            sys.stdout.write(json.dumps(_error(None, -32700, "Parse error")) + "\n")
            sys.stdout.flush()
            continue
        try:
            resp = handle(msg)
        except Exception as e:
            log(f"handler error: {type(e).__name__}: {e}")
            resp = _error(msg.get("id"), -32603, f"Internal error: {e}")
        if resp is not None:
            sys.stdout.write(json.dumps(resp) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
