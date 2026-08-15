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
import os
from urllib.parse import urlencode

import supercmo_env

from .. import catalog

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


def research_generate(route, payload, key):
    """Run one research call: resolve (platform, endpoint) -> SC path from the catalog, GET it with
    the query params + an x-api-key header, return {ok, platform, endpoint, data}. Never raises."""
    try:
        entry, query, err = _resolve(payload)
        if err:
            return err
        if not key:
            return {"ok": False, "error": "no research API key configured"}
        parsed, status, _detail = supercmo_env._request(
            entry.get("method", "GET"), _url(entry, query), headers={"x-api-key": key})
        if parsed is None:
            # Don't surface the vendor's raw error body — it can name the vendor, which would leak
            # into the (otherwise vendor-agnostic) agent surface. The status is enough for the caller.
            return {"ok": False, "error": f"research request failed ({status})"}
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
    print("scrapecreators OK")
