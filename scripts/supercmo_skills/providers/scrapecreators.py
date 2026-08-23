"""ScrapeCreators direct adapter — structured public data from social platforms and ad
libraries (profiles, posts, comments, competitor ads). BYOK: SCRAPECREATORS_API_KEY.

One read-only vendor behind a single call shape: GET {BASE}{path}?{query} with an `x-api-key`
header. The (platform, endpoint) pair selects the path and which params are valid, resolved from
the curated research catalog — the path is NEVER taken from the caller, so a request can't be
steered at an arbitrary URL (the catalog is the allow-list).

Same uniform contract as the media providers (BYOK_ENV / is_available / <cap>_generate /
<cap>_request_spec) so the router treats it like any other route. Returns structured data, not
media — no local persistence downstream.
"""
import json
import logging
import os
from urllib.parse import urlencode

import supercmo_env

from .. import catalog

logger = logging.getLogger(__name__)

BYOK_ENV = "SCRAPECREATORS_API_KEY"
KEY_ENABLES = "public social-platform research (profiles, posts, comments, competitor ads)"
KEY_SIGNUP = "scrapecreators.com"
_BASE = "https://api.scrapecreators.com"


def is_available():
    return bool(os.environ.get(BYOK_ENV))


def _resolve(payload):
    """(entry, query, None) for a valid (platform, endpoint, params), else (None, None, error).

    Validation is `catalog.research_validate`, so a dry_run surfaces exactly what a real call would.
    The SC path lives on the catalog entry, selected by the (platform, endpoint) enum — never
    supplied by the caller (the catalog is the allow-list)."""
    platform = (payload.get("platform") or "").strip().lower()
    endpoint = (payload.get("endpoint") or "").strip().lower()
    err = catalog.research_validate(platform, endpoint, payload.get("params"))
    if err:
        return None, None, {"ok": False, "error": err,
                            "hint": "call list_research_sources for the platforms, endpoints, and params"}
    entry = catalog.research_source(platform, endpoint)
    params = payload.get("params") or {}
    query = {k: v for k, v in params.items() if v is not None and str(v).strip() != ""}
    return entry, query, None


def _url(entry, query):
    # ponytail: GET + query only — every curated SC endpoint is a GET read. A POST endpoint (none
    # curated today) would carry method="POST" on the entry and send `query` as a body here.
    url = f"{_BASE}{entry['path']}"
    return f"{url}?{urlencode(query)}" if query else url


def _safe_vendor_message(detail):
    """The vendor's own error `message` when the body is JSON and carries one — and NOTHING else.
    Returns a stripped non-empty string or None. We surface only this field: the rest of the body can
    carry internal counters (e.g. the account's remaining credits), and the message itself is a plain
    validation string (e.g. "Invalid sort_by parameter. Needs to be one of: ...") that the agent can
    act on. Non-JSON or no `message` → None (caller falls back to a generic error)."""
    try:
        body = json.loads(detail) if isinstance(detail, str) else detail
    except (ValueError, TypeError):
        return None
    if isinstance(body, dict):
        msg = body.get("message")
        if isinstance(msg, str) and msg.strip():
            return msg.strip()
    return None


def research_generate(route, payload, key):
    """Run one research call: resolve (platform, endpoint) -> SC path from the catalog, GET it with
    the query params + an x-api-key header, return {ok, platform, endpoint, data}. Never raises."""
    try:
        entry, query, err = _resolve(payload)
        if err:
            return err
        if not key:
            return {"ok": False, "error": "no research API key configured"}
        parsed, status, detail = supercmo_env._request(
            entry.get("method", "GET"), _url(entry, query), headers={"x-api-key": key})
        if parsed is None:
            # The request reached the vendor and was rejected. A 400 is CALLER-FIXABLE — surface the
            # vendor's own message (a plain validation string) so the agent self-corrects; the vendor
            # is the source of truth on which params/values it accepts. Auth/rate/5xx are ours or
            # transient (not caller-fixable): keep the agent-facing error generic and log the raw body
            # server-side. We never return the raw body — it can carry internal counters.
            if status == 400:
                return {"ok": False, "error": _safe_vendor_message(detail) or "research request failed (400)"}
            logger.warning("research vendor error (status=%s): %s", status, (detail or "")[:300])
            return {"ok": False, "error": "research temporarily unavailable"}
        return {"ok": True, "platform": payload.get("platform"), "endpoint": payload.get("endpoint"),
                "data": parsed}
    except Exception as e:  # never raise out of *_generate
        return {"ok": False, "error": "research error", "detail": f"{type(e).__name__}: {e}"[:500]}


def research_request_spec(route, payload):
    """The exact request research_generate would send (key masked), for dry_run previews. Returns
    the same structured validation error a real call would on bad input."""
    entry, query, err = _resolve(payload)
    if err:
        return err
    return {"method": entry.get("method", "GET"), "url": _url(entry, query),
            "headers": {"x-api-key": "***"}}


if __name__ == "__main__":
    # ponytail: no-network self-check — catalog-driven URL build + validation.
    ok = research_request_spec(None, {"platform": "tiktok", "endpoint": "profile",
                                      "params": {"handle": "x"}})
    assert ok["url"] == f"{_BASE}/v1/tiktok/profile?handle=x", ok
    assert ok["headers"]["x-api-key"] == "***", ok
    bad = research_request_spec(None, {"platform": "tiktok", "endpoint": "profile", "params": {}})
    assert bad.get("ok") is False and "missing required params: handle" in bad["error"], bad
    unk = research_request_spec(None, {"platform": "nope", "endpoint": "nope", "params": {}})
    assert unk.get("ok") is False and "unknown research source" in unk["error"], unk
    # F21: _safe_vendor_message extracts ONLY the vendor `message` — never other body fields.
    _b = json.dumps({"message": "Invalid sort_by parameter. Needs to be one of: total_impressions, "
                     "relevancy_monthly_grouped", "credits_remaining": 999, "errorStatus": 400})
    assert _safe_vendor_message(_b) == ("Invalid sort_by parameter. Needs to be one of: "
                                        "total_impressions, relevancy_monthly_grouped"), _safe_vendor_message(_b)
    assert "credits_remaining" not in _safe_vendor_message(_b)     # never leaks the credit counter
    assert _safe_vendor_message(json.dumps({"success": False})) is None            # no message field
    assert _safe_vendor_message(json.dumps({"message": "   "})) is None            # blank message
    assert _safe_vendor_message("<html>500</html>") is None                        # non-JSON body
    assert _safe_vendor_message(None) is None
    print("scrapecreators OK")
