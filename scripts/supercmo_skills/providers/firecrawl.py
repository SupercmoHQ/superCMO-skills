"""Firecrawl direct adapter — structured extraction from a web page. BYOK: FIRECRAWL_API_KEY.

v2 scrape with a JSON format returns prompt/schema-guided structured data:
  POST /v2/scrape  body {url, formats:[{type:"json", prompt, schema}]}
  -> {success, data:{json:{...extracted...}, metadata:{...}}}

Same uniform contract as the media providers (BYOK_ENV / is_available / <cap>_generate /
<cap>_request_spec) so the router treats it like any other route. Returns structured data, not
media — no local persistence downstream.
"""
import json
import os

import supercmo_env

BYOK_ENV = "FIRECRAWL_API_KEY"
KEY_ENABLES = "url extraction (product / web pages)"
KEY_SIGNUP = "firecrawl.dev"
_BASE = "https://api.firecrawl.dev/v2"


def is_available():
    return bool(os.environ.get(BYOK_ENV))


def _build_extract_input(route, payload):
    """v2 /scrape body requesting a single JSON extraction format."""
    fmt = {"type": "json"}
    if payload.get("prompt"):
        fmt["prompt"] = payload["prompt"]
    if payload.get("schema"):
        fmt["schema"] = payload["schema"]
    return {"url": payload["url"], "formats": [fmt]}


def extract_generate(route, payload, key):
    try:
        parsed, status, err = supercmo_env._request(
            "POST", f"{_BASE}/scrape", body=_build_extract_input(route, payload),
            headers={"Authorization": f"Bearer {key}"})
        if parsed is None:
            return {"ok": False, "error": f"firecrawl extract failed ({status})", "detail": (err or "")[:500]}
        data = parsed.get("data") or {}
        if data.get("json") is None:
            return {"ok": False, "error": "firecrawl returned no structured data",
                    "detail": json.dumps(parsed)[:300]}
        return {"ok": True, "model": payload.get("model"),
                "data": data.get("json"), "metadata": data.get("metadata")}
    except Exception as e:  # never raise out of *_generate
        return {"ok": False, "error": "firecrawl extract error", "detail": f"{type(e).__name__}: {e}"[:500]}


def extract_request_spec(route, payload):
    return {"method": "POST", "url": f"{_BASE}/scrape",
            "headers": {"Authorization": "Bearer ***", "Content-Type": "application/json"},
            "body": _build_extract_input(route, payload)}
