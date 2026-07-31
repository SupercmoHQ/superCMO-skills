#!/usr/bin/env python3
"""SuperCMO generation MCP server — JSON-RPC stdio plumbing.

Exposes the generation tools (see tools/) over MCP stdio.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))

import registry
import tools  # noqa: F401,E402 (registers tools on import)

try:
    from supercmo_skills import telemetry  # noqa: E402 — anonymous, opt-out usage counts
except Exception:  # telemetry is best-effort; never block the server on it
    telemetry = None
if telemetry is not None:
    try:
        telemetry.set_surface("mcp")
    except Exception:
        pass

# Generation tools telemeter inside the shared client (supercmo_skills._dispatch), with
# route + model; the dispatch hook below covers only the rest (e.g. list_* discovery).
_GEN_TOOLS = {"image_generate", "video_generate", "text_to_speech", "url_extraction", "image_analysis"}

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
        _t0 = time.monotonic()
        _err = None
        try:
            out = fn(params.get("arguments") or {})
        except Exception as e:
            log(f"tool {name} raised: {type(e).__name__}: {e}")
            _err = type(e).__name__
            out = {"ok": False, "error": f"{type(e).__name__}: {e}"}
        if telemetry is not None and name not in _GEN_TOOLS:
            try:  # telemetry must never break a tool call, even if record() were buggy
                # tool NAME only — never the arguments (they carry user prompts).
                telemetry.record(name, bool(out.get("ok", False)),
                                 int((time.monotonic() - _t0) * 1000), error_class=_err)
            except Exception:
                pass
        return _result(req_id, {
            "content": [{"type": "text", "text": json.dumps(out, indent=2)}],
            "isError": not out.get("ok", False),
        })

    if req_id is None:
        return None
    return _error(req_id, -32601, f"Method not found: {method}")


def main():
    # Credentials come from ~/.supercmo/.env, which supercmo_env.py loads on import (see
    # scripts/supercmo_env.py). Any credential the host injects into this process's env is honored too.
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
