"""Firecrawl direct adapter — structured extraction from a web page. BYOK: FIRECRAWL_API_KEY.

With a prompt or schema, v2 scrape's JSON format returns guided structured data (5 credits):
  POST /v2/scrape  body {url, formats:[{type:"json", prompt, schema}, "branding", {type:"screenshot"}]}
  -> {success, data:{json:{...}, branding:{colors, fonts, typography, ...}, screenshot, metadata:{...}}}
Without either, it returns the page's own text as markdown instead (1 credit): the caller's model reads
it, which captures as much as the JSON reader at a fifth of the cost.

The JSON format is an LLM reading the page's text, which carries no CSS: asked for colours or fonts it
guesses. The branding format reads them from the rendered page, and the screenshot shows the page as a
visitor first sees it; neither costs an extra Firecrawl credit. Of branding, only what a brand profile
uses is passed on, and its image fields only as URLs: an inline logo can be 20 KB+.

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
_SCREENSHOT = {"type": "screenshot", "fullPage": False}
PAGE_CHARS = 60_000  # ponytail: a homepage's main content is ~30K; past this, the rest is cut and flagged


def is_available():
    return bool(os.environ.get(BYOK_ENV))


def is_structured(payload):
    """A prompt or schema asks for the JSON reader; without either the page's own text comes back."""
    return bool(payload.get("prompt") or payload.get("schema"))


def _build_extract_input(route, payload):
    """v2 /scrape body: the JSON extraction or the page's text, plus its rendered branding and a screenshot."""
    if not is_structured(payload):
        return {"url": payload["url"], "formats": ["markdown", "branding", _SCREENSHOT]}
    fmt = {"type": "json"}
    if payload.get("prompt"):
        fmt["prompt"] = payload["prompt"]
    if payload.get("schema"):
        fmt["schema"] = payload["schema"]
    return {"url": payload["url"], "formats": [fmt, "branding", _SCREENSHOT]}


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
        branding, shot = _branding(data.get("branding")), _url_only(data.get("screenshot"))
        if is_structured(payload):
            out = data.get("json")
        else:
            md = data.get("markdown") or ""
            # A page with no text (a single-page app) still hands back what it renders.
            out = {"markdown": md[:PAGE_CHARS], "truncated": len(md) > PAGE_CHARS} if (md or branding or shot) else None
        if out is None:
            return {"ok": False, "error": "firecrawl returned no " + ("structured data" if is_structured(payload) else "page text"),
                    "detail": json.dumps(parsed)[:300]}
        return {"ok": True, "model": payload.get("model"),
                "data": out, "branding": branding, "screenshot": shot, "metadata": data.get("metadata")}
    except Exception as e:  # never raise out of *_generate
        return {"ok": False, "error": "firecrawl extract error", "detail": f"{type(e).__name__}: {e}"[:500]}


def extract_request_spec(route, payload):
    return {"method": "POST", "url": f"{_BASE}/scrape",
            "headers": {"Authorization": "Bearer ***", "Content-Type": "application/json"},
            "body": _build_extract_input(route, payload)}
