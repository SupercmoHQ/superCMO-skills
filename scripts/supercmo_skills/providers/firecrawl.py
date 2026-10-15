"""Firecrawl direct adapter — structured extraction from a web page. BYOK: FIRECRAWL_API_KEY.

With a prompt or schema, v2 scrape's JSON format returns guided structured data (5 credits):
  POST /v2/scrape  body {url, formats:[{type:"json", prompt, schema}]}
  -> {success, data:{json:{...}, metadata:{...}}}
Without either, it returns the page's own text instead (1 credit), with the colours, fonts and logo the
page renders (branding) and a screenshot of it as a visitor first sees it:
  POST /v2/scrape  body {url, formats:["markdown", "branding", {type:"screenshot"}]}
  -> {success, data:{markdown, branding:{colors, fonts, typography, ...}, screenshot, metadata:{...}}}
The caller's model reads the text, which captures as much as the JSON reader. Branding is asked for only
here: it bypasses Firecrawl's cache.
Of branding, only what a brand profile uses is passed on, and its image fields only as URLs: an inline
logo can be 20 KB+. A page that answers HTTP 400 or above is a failed read, whatever came back with it.

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
_BRANDING_KEYS = ("colorScheme", "colors", "fonts", "typography", "logo", "images")
_PAGE_FORMATS = ["markdown", "branding", {"type": "screenshot", "fullPage": False}]
PAGE_CHARS = 60_000  # ponytail: a homepage's main content is ~30K; past this, the rest is cut and flagged


def is_available():
    return bool(os.environ.get(BYOK_ENV))


def is_structured(payload):
    """A prompt or schema asks for the JSON reader; without either the page's own text comes back."""
    return bool(payload.get("prompt") or payload.get("schema"))


def _build_extract_input(route, payload):
    """v2 /scrape body: the JSON extraction alone, or the page's text with its branding and a screenshot."""
    if not is_structured(payload):
        return {"url": payload["url"], "formats": list(_PAGE_FORMATS)}
    fmt = {"type": "json"}
    if payload.get("prompt"):
        fmt["prompt"] = payload["prompt"]
    if payload.get("schema"):
        fmt["schema"] = payload["schema"]
    return {"url": payload["url"], "formats": [fmt]}


def _url_only(v):
    return v if isinstance(v, str) and v.startswith(("http://", "https://")) else None


def _branding(b):
    """The parts of Firecrawl's branding a brand profile uses, with image fields kept only as URLs."""
    if not isinstance(b, dict):
        return None
    out = {k: b[k] for k in _BRANDING_KEYS if b.get(k) not in (None, "", {}, [])}
    if "logo" in out:
        out["logo"] = _url_only(out["logo"])
    if isinstance(out.get("images"), dict):
        kept = {k: (v if k == "logoAlt" else _url_only(v)) for k, v in out["images"].items()}
        out["images"] = {k: v for k, v in kept.items() if v}
    out = {k: v for k, v in out.items() if v not in (None, {}, [])}
    return out or None


def extract_generate(route, payload, key):
    try:
        parsed, status, err = supercmo_env._request(
            "POST", f"{_BASE}/scrape", body=_build_extract_input(route, payload),
            headers={"Authorization": f"Bearer {key}"})
        if parsed is None:
            return {"ok": False, "error": f"firecrawl extract failed ({status})", "detail": (err or "")[:500]}
        data = parsed.get("data") or {}
        metadata = data.get("metadata")
        page_status = (metadata or {}).get("statusCode")
        if isinstance(page_status, int) and page_status >= 400:
            return {"ok": False, "error": f"the page answered HTTP {page_status}", "metadata": metadata}
        if is_structured(payload):
            if data.get("json") is None:
                return {"ok": False, "error": "firecrawl returned no structured data",
                        "detail": json.dumps(parsed)[:300]}
            return {"ok": True, "model": payload.get("model"), "data": data.get("json"), "metadata": metadata}
        branding, shot = _branding(data.get("branding")), _url_only(data.get("screenshot"))
        md = data.get("markdown") or ""
        if not (md or branding or shot):
            return {"ok": False, "error": "firecrawl returned no page text", "detail": json.dumps(parsed)[:300]}
        # A page with no text (a single-page app) still hands back what it renders.
        return {"ok": True, "model": payload.get("model"),
                "data": {"markdown": md[:PAGE_CHARS], "truncated": len(md) > PAGE_CHARS},
                "branding": branding, "screenshot": shot, "metadata": metadata}
    except Exception as e:  # never raise out of *_generate
        return {"ok": False, "error": "firecrawl extract error", "detail": f"{type(e).__name__}: {e}"[:500]}


def extract_request_spec(route, payload):
    return {"method": "POST", "url": f"{_BASE}/scrape",
            "headers": {"Authorization": "Bearer ***", "Content-Type": "application/json"},
            "body": _build_extract_input(route, payload)}
