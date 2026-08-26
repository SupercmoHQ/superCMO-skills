"""Shape a research response before it reaches the agent.

`social_research` forwards a vendor's JSON verbatim. For the ad libraries that payload is mostly
unreadable bulk — signed CDN query strings, every crop of every image, five URL variants per video,
the advertiser's profile picture repeated on all thirty ads. On a measured 30-ad page of
`meta_ad_library/company_ads`: 185,210 characters, of which 31% was signed URLs and ~18% was
everything the caller actually reads.

Four things happen here, in order:

0. **Placement.** Each run gets a directory for its responses and an output directory for whatever
   is built from them, both settled here so a caller never resolves them from its own cwd.
1. **Projection.** Endpoints with a known shape are projected to their useful fields and a single
   media URL per ad, with the facts that belong to the advertiser rather than the ad — its name,
   following and category — carried once in `advertisers` instead of repeated on every row. The
   caller can widen this with `fields`, or opt out with `fields="*"`.
2. **Persistence.** Every response is written to a file and the call returns its path, so a caller
   feeding responses to a script always has one and never has to serialise a payload back out of the
   conversation to produce it. A response too large to read comes back as the path alone, with the
   count and the cursor — a documented return shape, not an accident of whatever harness the agent
   runs in.
3. **Disclosure.** Whatever was dropped is named in `shaping` on the response. Nothing is removed
   silently.

Projections are only written for endpoints whose shape is known from real responses. Every other
endpoint passes through untouched except for the size guard, so a new source is never silently
mangled.
"""

import datetime
import json
import os
import tempfile
from urllib.parse import parse_qsl, urlsplit

from . import paths

# Roughly 15k tokens. Past this a response stops being something an agent can read and starts being
# something it has to process, so it goes to a file and the caller gets a path.
MAX_INLINE_CHARS = 60_000

RAW = "*"


# --------------------------------------------------------------------- meta ad library

def _first_media(snapshot):
    """One playable URL and its kind. The vendor ships five variants per video and every crop of
    every image; the caller needs one of them and can ask for the rest with fields="*"."""
    videos = list(snapshot.get("videos") or [])
    images = list(snapshot.get("images") or [])
    for card in snapshot.get("cards") or []:
        if card.get("video_sd_url") or card.get("video_hd_url"):
            videos.append(card)
        elif card.get("original_image_url") or card.get("resized_image_url"):
            images.append(card)
    if videos:
        v = videos[0]
        return v.get("video_sd_url") or v.get("video_hd_url"), "video", len(videos)
    if images:
        i = images[0]
        return i.get("original_image_url") or i.get("resized_image_url"), "image", len(images)
    return None, None, 0


# Ad copy long enough to dominate a page is rare, and a caller reading structure rather than wording
# does not need all of it. The cut is disclosed per row, and fields="*" returns the full text.
BODY_CHARS = 400

# A card's body is one panel of an argument, not the whole of it.
CARD_CHARS = 200

# Click-tracking parameters, dropped from the landing URL so two ads on one offer compare equal.
TRACKING_PREFIXES = ("utm_", "fbclid", "gclid", "ttclid", "epik", "_branch", "wickedid")


def _as_date(text):
    if not isinstance(text, str) or len(text) < 10:
        return None
    try:
        return datetime.date.fromisoformat(text[:10])
    except ValueError:
        return None


def _days_running(ad, today):
    """The ad's own run length where it carries one, else derived from its dates. None when the ad
    carries no usable date at all — never zero, which would read as "ran and stopped the same day"."""
    active = ad.get("total_active_time")
    if isinstance(active, (int, float)) and active > 0:
        return int(active // 86400)
    start = _as_date(ad.get("start_date_string"))
    if not start:
        return None
    # A live ad's end date is only the day the library was read, so it is ignored while live.
    end = today if ad.get("is_active") else (_as_date(ad.get("end_date_string")) or today)
    return max(0, (end - start).days)


def _campaign(url, caption):
    """Ads pointing at the same offer are one campaign: domain plus first path segment."""
    if not url:
        return f"(no link) {caption or ''}".strip()
    parts = urlsplit(url)
    host = parts.netloc.lower()
    host = host[4:] if host.startswith("www.") else host
    segments = parts.path.strip("/").split("/")
    seg = segments[0] if segments and segments[0] else ""
    return f"{host}/{seg}" if seg else host


def _intent(url):
    """prospecting / retargeting, where the tracking parameters say so."""
    if not url:
        return None
    blob = " ".join(v for _, v in parse_qsl(urlsplit(url).query)).lower()
    if "retarget" in blob or "remarket" in blob or "rtg" in blob:
        return "retargeting"
    if "prospect" in blob or "acq" in blob or "cold" in blob:
        return "prospecting"
    return None


def _clean_url(url):
    if not url:
        return ""
    parts = urlsplit(url)
    kept = [(k, v) for k, v in parse_qsl(parts.query)
            if not any(k.lower().startswith(p) for p in TRACKING_PREFIXES)]
    query = "&".join(f"{k}={v}" for k, v in kept)
    return f"{parts.scheme}://{parts.netloc}{parts.path}" + (f"?{query}" if query else "")


def _creative_kind(snapshot, media_kind):
    """video / image, or the composite the display format makes of it."""
    fmt = (snapshot.get("display_format") or "").upper()
    if not media_kind:
        return fmt.lower() or None
    if fmt == "CAROUSEL":
        return "carousel"
    if fmt == "DCO":
        return "dco-" + media_kind
    return media_kind


def _project_ad(ad, today=None):
    """One ad, flat, with the facts a reader has to derive by hand already derived.

    `days_running`, `campaign` and `intent` are computed here rather than left to the caller: each
    has a wrong-looking answer that is easy to reach (counting a live ad's end date, clustering on
    the tracking parameters, treating a missing date as zero) and no reason to be reached twice."""
    today = today or datetime.date.today()
    snap = ad.get("snapshot") or {}
    body = snap.get("body")
    text = body.get("text") if isinstance(body, dict) else body
    truncated = False
    if isinstance(text, str) and len(text) > BODY_CHARS:
        text, truncated = text[:BODY_CHARS], True
    media_url, media_kind, media_count = _first_media(snap)
    link = snap.get("link_url") or ""
    if not link:
        for card in snap.get("cards") or []:
            link = card.get("link_url") or ""
            if link:
                break

    # A carousel or DCO ad carries its argument across its cards, not in the top-level copy.
    cards = []
    for card in snap.get("cards") or []:
        kept = {}
        for k in ("title", "body", "cta_text", "link_description", "link_url"):
            v = card.get(k)
            if not v:
                continue
            kept[k] = v[:CARD_CHARS] if k == "body" and isinstance(v, str) else v
        if kept:
            cards.append(kept)

    row = {
        "ad_archive_id": ad.get("ad_archive_id"),
        "page_id": ad.get("page_id"),
        "page_name": ad.get("page_name") or snap.get("page_name"),
        "variant_group": ad.get("collation_id"),
        "status": "live" if ad.get("is_active") else "stopped",
        "first_seen": (ad.get("start_date_string") or "")[:10] or None,
        "last_seen": None if ad.get("is_active") else ((ad.get("end_date_string") or "")[:10] or None),
        "days_running": _days_running(ad, today),
        "captured": today.isoformat(),
        "creative_kind": _creative_kind(snap, media_kind),
        "publisher_platform": ad.get("publisher_platform"),
        "variants": ad.get("collation_count"),
        "cta_text": snap.get("cta_text"),
        "cta_type": snap.get("cta_type"),
        "title": snap.get("title"),
        "body_text": text,
        "landing_url": _clean_url(link),
        "campaign": _campaign(link, snap.get("caption")),
        "intent": _intent(link),
        "link_description": snap.get("link_description"),
        "media_url": media_url,
        "media_count": media_count,
        "library_url": ad.get("url"),
        "cards": cards or None,
        "branded_content": bool(snap.get("branded_content")) or None,
    }
    if truncated:
        row["body_truncated"] = True
    return row


def _project_company(company):
    return {
        "page_id": company.get("page_id") or company.get("id"),
        "name": company.get("name") or company.get("page_name"),
        "category": company.get("category"),
        "verification": company.get("verification") or company.get("is_verified"),
        "likes": company.get("likes") or company.get("page_like_count"),
        "country": company.get("country"),
        "ig_username": company.get("ig_username"),
    }


# Endpoints whose response shape is known from real payloads. Anything not listed passes through.
PROJECTIONS = {
    ("meta_ad_library", "company_ads"): _project_ad,
    ("meta_ad_library", "search_ads"): _project_ad,
    ("meta_ad_library", "search_companies"): _project_company,
}

# The vendor calls the same list different things on different endpoints.
LIST_KEYS = ("results", "searchResults", "companies", "ads", "data")


def _find_list(data):
    for key in LIST_KEYS:
        value = data.get(key)
        if isinstance(value, list):
            return key, value
    return None, None


def _select(row, fields):
    return {k: row.get(k) for k in fields if k in row}


def project(platform, endpoint, data, fields=None):
    """Return (data, shaping). `fields` is None for the endpoint's default projection, "*" for the
    vendor's payload untouched, or a list of field names to keep from the projected row."""
    if not isinstance(data, dict):
        return data, None
    if fields == RAW or (isinstance(fields, (list, tuple)) and RAW in fields):
        return data, {"projected": False, "reason": 'fields="*" — vendor payload untouched'}

    projector = PROJECTIONS.get((platform, endpoint))
    if projector is None:
        note = None
        if fields:
            note = "fields ignored — no projection is defined for this endpoint yet"
        return data, ({"projected": False, "reason": note} if note else None)

    list_key, rows = _find_list(data)
    if rows is None:
        return data, None

    projected = [projector(r) for r in rows if isinstance(r, dict)]
    if fields:
        projected = [_select(r, fields) for r in projected]

    before = len(json.dumps(data, default=str))
    # Only the ad endpoints carry page-level facts worth hoisting; a company row already is the
    # advertiser, so lifting one out of it would just restate the row with the fields renamed.
    advertisers = {}
    if projector is _project_ad:
        for raw, row in zip(rows, projected):
            snap = raw.get("snapshot") or {}
            pid = row.get("page_id")
            if pid and pid not in advertisers:
                advertisers[pid] = {
                    "name": row.get("page_name"),
                    "likes": snap.get("page_like_count"),
                    "categories": snap.get("page_categories"),
                }

    shaped = {
        "results": projected,
        "total": data.get("searchResultsCount") or data.get("total") or len(projected),
        "cursor": data.get("cursor") or None,
    }
    if advertisers:
        shaped["advertisers"] = advertisers
    for passthrough in ("credits_remaining", "credits_charged", "success"):
        if passthrough in data:
            shaped[passthrough] = data[passthrough]
    after = len(json.dumps(shaped, default=str))

    return shaped, {
        "projected": True,
        "returned": len(projected),
        "source_list_key": list_key,
        "chars_before": before,
        "chars_after": after,
        "dropped": "media variants beyond the first, image crops, profile images, and vendor "
                   "bookkeeping fields",
        "truncated": (f"body text over {BODY_CHARS} chars, flagged per row as body_truncated"
                      if any(r.get("body_truncated") for r in projected) else None),
        "raw_available": 'call again with fields="*" for the vendor payload',
    }


_SESSION = {"dir": None, "n": 0, "pulled": False, "out": None}

# A research run starts by resolving an advertiser, then pulls its ads. Seeing a fresh lookup after
# ads have already been pulled means a new run has begun, and it gets its own directory — otherwise
# a second run in one session would inherit the first run's competitors.
_LOOKUP_ENDPOINTS = ("search_companies",)


def _next_path(platform, endpoint):
    """A file per call, under a directory per research run."""
    starting_over = endpoint in _LOOKUP_ENDPOINTS and _SESSION["pulled"]
    if _SESSION["dir"] is None or starting_over:
        stamp = datetime.datetime.now().strftime("%Y-%m-%d-%H%M")
        # The run's output folder is settled here, in the server, where the working directory is the
        # caller's project — the same anchor generated media uses. A consumer running elsewhere is
        # told where to write rather than resolving it from its own cwd.
        _SESSION.update(dir=tempfile.mkdtemp(prefix=f"supercmo_research_{stamp}_"),
                        n=0, pulled=False, out=paths.research_dir())
    if endpoint not in _LOOKUP_ENDPOINTS:
        _SESSION["pulled"] = True
    _SESSION["n"] += 1
    return os.path.join(_SESSION["dir"], f"{platform}-{endpoint}-{_SESSION['n']:03d}.json")


def persist(payload, platform, endpoint, max_chars=MAX_INLINE_CHARS):
    """Write every response to disk, and say whether it also fits in the conversation.

    The file is written whatever the size, so a caller processing responses with a script always has
    a path to hand it and never has to serialise a payload back out of the conversation to get one.
    `inline` says whether `data` came back as well; where it did not, the file is the only copy.

    Returns (payload, saved)."""
    encoded = json.dumps(payload, default=str)
    path = _next_path(platform, endpoint)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(encoded)

    data = payload.get("data") if isinstance(payload, dict) else None
    _, rows = _find_list(data) if isinstance(data, dict) else (None, None)
    inline = len(encoded) <= max_chars

    saved = {
        "path": path,
        "output_dir": _SESSION["out"],
        "inline": inline,
        "chars": len(encoded),
        "count": len(rows) if rows is not None else None,
        "total": (data or {}).get("total") or (data or {}).get("searchResultsCount"),
        "cursor": (data or {}).get("cursor"),
    }
    if not inline:
        saved["reason"] = (f"response is {len(encoded):,} characters, over the {max_chars:,} "
                           f"inline limit, so `data` was left out of this reply")
        saved["hint"] = ("the full JSON is at `path` — process it with a script, or narrow the "
                         "call with fields")
    return payload, saved
