#!/usr/bin/env python3
"""SuperCMO environment + routing helpers (standard library only).

Every network script imports this first.

Credentials come from the process environment only — the MCP standard for stdio
servers (the Authorization spec: stdio servers "retrieve credentials from the
environment"). The host populates that environment via its MCP config `env`
block — Claude `.mcp.json`, Cursor `.cursor/mcp.json`, Codex
`~/.codex/config.toml` `[mcp_servers.*.env]` — or the user exports the vars in
their shell. This module never reads a bespoke credentials file.

Route resolution — vendor calls pick their path in priority order:
  BYOK (direct vendor key in env) -> SUPERCMO_API_KEY (the metered proxy at
  SUPERCMO_API_URL) -> actionable error.
User-account calls resolve: raw token in env -> token handout from the
connections endpoint -> actionable error.

CLI:
  supercmo_env.py --status    # which keys are present in the environment
  supercmo_env.py --dry-run   # no network calls — prints a notice
"""
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_API_URL = "https://api.getsupercmo.ai"
PROXY_BASE = "/api/v1/supercmo/proxy"
CONNECTIONS_BASE = "/api/v1/supercmo/connections"
ME_PATH = "/api/v1/supercmo/me"
RETRIES = 3
BACKOFF = [1, 2, 4]
# Browser-like UA so Cloudflare's bot protection fronting the API doesn't 403 the
# sandbox's stdlib-urllib calls: urllib's default "Python-urllib/x.y" UA trips
# Cloudflare's managed bot rule (HTTP 403, "error code: 1010"). A plausible browser
# UA passes (verified). Callers may override with a User-Agent in `headers`.
_USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
               "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

def api_url():
    return (os.environ.get("SUPERCMO_API_URL") or DEFAULT_API_URL).rstrip("/")


def supercmo_key():
    return os.environ.get("SUPERCMO_API_KEY")


def resolve_vendor_route(*byok_vars):
    """('direct', None) when any BYOK var is set; ('proxy', key) when the
    SuperCMO key is available; ('none', hint) otherwise."""
    for var in byok_vars:
        if os.environ.get(var):
            return "direct", None
    key = supercmo_key()
    if key:
        return "proxy", key
    hint = (f"Set {' or '.join(byok_vars)} in your environment (bring your own key), or run the "
            "supercmo-setup skill for a guided check. Or use a managed SuperCMO key — buy credits + "
            "mint a key at getsupercmo.ai/settings?tab=keys.")
    return "none", hint


def _request(method, url, body=None, headers=None, timeout=120):
    """JSON request with retries. Returns (parsed, status, error)."""
    data = json.dumps(body).encode("utf-8") if body is not None else None
    hdrs = {"Content-Type": "application/json", "User-Agent": _USER_AGENT, **(headers or {})}
    last_err, last_status = None, None
    for attempt in range(RETRIES):
        req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8")), resp.status, None
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:500]
            last_err, last_status = detail, e.code
            if e.code in (400, 401, 402, 403, 404, 429):
                return None, e.code, detail  # no retry on client errors / rate limits
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            last_err = f"{type(e).__name__}: {e}"
        time.sleep(BACKOFF[min(attempt, len(BACKOFF) - 1)])
    return None, last_status, last_err


def _request_raw(method, url, body=None, headers=None, timeout=120):
    """Like _request but returns the raw response bytes (for binary responses, e.g. audio).
    Returns (data_bytes, content_type, status, error)."""
    data = json.dumps(body).encode("utf-8") if body is not None else None
    hdrs = {"Content-Type": "application/json", "User-Agent": _USER_AGENT, **(headers or {})}
    last_err, last_status = None, None
    for attempt in range(RETRIES):
        req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read(), resp.headers.get("Content-Type", ""), resp.status, None
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:500]
            last_err, last_status = detail, e.code
            if e.code in (400, 401, 402, 403, 404, 429):
                return None, None, e.code, detail
        except (urllib.error.URLError, TimeoutError) as e:
            last_err = f"{type(e).__name__}: {e}"
        time.sleep(BACKOFF[min(attempt, len(BACKOFF) - 1)])
    return None, None, last_status, last_err


def proxy_request(capability, body, method="POST", call_id=None, timeout=120):
    """Call the metered proxy. Returns the parsed response dict, or a
    structured {'ok': False, ...} error the caller can print and exit on.
    402 -> insufficient_credits (the agent should relay an upgrade prompt).
    timeout bounds the call — managed video/tts block server-side on the vendor queue (~minutes)."""
    key = supercmo_key()
    if not key:
        return {"ok": False, "error": "SUPERCMO_API_KEY missing — cannot use the metered proxy."}
    headers = {"Authorization": f"Bearer {key}"}
    if call_id:
        body = dict(body or {})
        body.setdefault("call_id", call_id)
    url = f"{api_url()}{PROXY_BASE}/{capability.lstrip('/')}"
    parsed, status, err = _request(method, url, body=body if method != "GET" else None,
                                   headers=headers, timeout=timeout)
    if parsed is not None:
        return parsed
    if status == 402:
        return {"ok": False, "error": "insufficient_credits",
                "action": "upgrade", "detail": err,
                "topup": "getsupercmo.ai/settings?tab=billing"}
    if status == 429:
        return {"ok": False, "error": "rate_limited", "detail": err,
                "fix": "the social gateway is rate-limiting; wait for the cooldown before retrying."}
    if status in (401, 403):
        return {"ok": False, "error": "supercmo_key_rejected",
                "detail": err, "fix": "re-issue the key in Settings -> API Keys"}
    return {"ok": False, "error": f"proxy {capability} failed ({status}): {err}"}


def proxy_spec(capability, body):
    """Dry-run shape for proxy-routed calls."""
    return {
        "method": "POST",
        "url": f"{api_url()}{PROXY_BASE}/{capability.lstrip('/')}",
        "headers": {"Authorization": "Bearer SUPERCMO_API_KEY", "Content-Type": "application/json"},
        "body": body,
    }


def get_connection_token(service):
    """Short-lived user-account token via the connections handout.
    Returns (token, None) or (None, structured_error_dict)."""
    key = supercmo_key()
    if not key:
        return None, {"ok": False, "error": f"No {service} token in env and no SUPERCMO_API_KEY for the token handout."}
    url = f"{api_url()}{CONNECTIONS_BASE}/{urllib.parse.quote(service)}/token"
    parsed, status, err = _request("GET", url, headers={"Authorization": f"Bearer {key}"})
    if parsed and parsed.get("access_token"):
        return parsed["access_token"], None
    if status == 404 or (parsed and parsed.get("error") == "not_connected"):
        return None, {"ok": False, "error": "not_connected", "service": service,
                      "fix": f"Connect {service} in the superCMO app (Integrations page), then retry."}
    return None, {"ok": False, "error": f"token handout for {service} failed ({status}): {err}"}


def main():
    args = sys.argv[1:]
    if "--dry-run" in args:
        print(json.dumps({"_dry_run": True, "method": None, "url": None, "headers": None, "body": None,
                          "note": "supercmo_env is a local env loader/router — no API calls on its own"}, indent=2))
        return
    interesting = ["SUPERCMO_API_KEY", "SUPERCMO_API_URL", "FIRECRAWL_API_KEY", "FIRECRAWL_API_URL",
                   "GSC_ACCESS_TOKEN", "META_ACCESS_TOKEN", "IG_ACCESS_TOKEN", "WAVESPEED_API_KEY",
                   "SEEDANCE_API_KEY", "POSTIZ_API_KEY", "YOUTUBE_API_KEY", "PAGESPEED_API_KEY"]
    print(json.dumps({
        "ok": True,
        "source": "process environment (host MCP config env block / shell export)",
        "api_url": api_url(),
        "keys_present": {k: bool(os.environ.get(k)) for k in interesting},
    }, indent=2))


if __name__ == "__main__":
    main()
