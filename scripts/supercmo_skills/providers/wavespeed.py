"""WaveSpeed provider — one queued API for both image and video (api.wavespeed.ai/api/v3).

Uniform provider contract (identical to providers/fal.py — the client dispatches on it):
  BYOK_ENV                            env var whose presence means "use me directly"
  is_available()                      True when that key is set
  <cap>_generate(route, payload, key) run a generation; payload = semantic input
  <cap>_submit / <cap>_status         the queued split (submit here, rejoin in a later tool call)
  <cap>_request_spec(route, payload)  dry-run shape (key masked)

`route` carries this provider's per-model config (id / edit_id / sizes / supports / media / …) from
the catalog, so the provider owns its own ids + constraints.

WaveSpeed differs from fal in three ways that matter here:
  * ONE submit path for every capability — `POST /api/v3/{model_id}` — and ONE poll URL that
    returns status *and* outputs together (fal needs a second fetch on COMPLETED). We still return
    the fal-shaped {status_url, response_url} from submit (both set to that one URL) so the client's
    job handle, wait loop and rejoin are provider-agnostic.
  * results are a bare `data.outputs` URL array for every capability — no width/height/duration.
  * `Authorization: Bearer` (fal uses `Key`).

MAX_PARALLEL is the *Bronze* (default, no top-up) concurrency ceiling: ~10 images/min, 5 videos/min,
3 concurrent tasks. Silver ($100 top-up) raises it to 100 concurrent and Gold to 200, but a fresh
key gets Bronze, so the batch tools fan out to this floor rather than 429-ing on someone's first run.
"""
import base64
import json
import os
import time
import uuid

import supercmo_env

BASE = "https://api.wavespeed.ai/api/v3"
BYOK_ENV = "WAVESPEED_API_KEY"
KEY_ENABLES = "image · video"
KEY_SIGNUP = "wavespeed.ai"
MAX_PARALLEL = 3         # Bronze-tier concurrent tasks; see the module docstring
_UPLOAD = f"{BASE}/media/upload/binary"
_STATUS_POLL_TIMEOUT = 15   # per status poll: short + single attempt, so one unanswered poll can't
                            # freeze the caller's wait budget (the caller paces its own retry loop)
_PENDING_STATES = ("created", "processing")
_POLL_INTERVAL = 3       # seconds between status polls on the blocking path
_MAX_POLLS = 150         # ceiling ≈ 450s sleep + per-poll network, kept UNDER the MCP client's 600s
                         # per-call timeout so the tool returns its own clean "timed out" instead of
                         # being hard-killed by the caller
_UPLOAD_EXT = {"image/jpeg": ".jpg", "image/jpg": ".jpg", "image/png": ".png", "image/webp": ".webp",
               "video/mp4": ".mp4", "video/quicktime": ".mov", "video/webm": ".webm",
               "audio/mpeg": ".mp3", "audio/mp3": ".mp3", "audio/wav": ".wav"}


def is_available():
    return bool(os.environ.get(BYOK_ENV))


def _headers(key):
    return {"Authorization": f"Bearer {key}"}


def _data(parsed):
    """The `data` envelope every WaveSpeed response wraps its payload in."""
    d = (parsed or {}).get("data")
    return d if isinstance(d, dict) else {}


def _reason(raw):
    """The readable reason out of an error body — a content-checker rejection, a rejected input.
    WaveSpeed answers `{"code": 4xx, "message": "...", "data": {"error": "..."}}`. None if neither."""
    try:
        body = json.loads(raw)
    except (TypeError, ValueError):
        return None
    if not isinstance(body, dict):
        return None
    return _data(body).get("error") or body.get("message") or None


# --------------------------------------------------------------------- media hosting (multipart)
def _multipart(data, content_type, file_name):
    """A one-field (`file`) multipart body, built by hand — this package is stdlib-only, so there is
    no requests/urllib3 to lean on. Returns (body_bytes, content_type_header)."""
    boundary = f"----supercmo{uuid.uuid4().hex}"
    head = (f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{file_name}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n").encode("utf-8")
    return head + data + f"\r\n--{boundary}--\r\n".encode("utf-8"), \
        f"multipart/form-data; boundary={boundary}"


def _upload(data, content_type, file_name, key):
    """Upload bytes to WaveSpeed storage → hosted download_url (or None on failure). Files are kept
    for 7 days, which is far longer than any generation needs."""
    body, ct = _multipart(data, content_type, file_name)
    raw, _rct, status, _err = supercmo_env._request_raw(
        "POST", _UPLOAD, raw_body=body, content_type=ct, timeout=180, retries=1,
        headers={**_headers(key), "Accept": "application/json"})
    if status not in (200, 201) or not raw:
        return None
    try:
        return _data(json.loads(raw.decode("utf-8"))).get("download_url")
    except (ValueError, UnicodeDecodeError):
        return None


def _ensure_hosted(value, key):
    """A local data: URI → uploaded WaveSpeed URL; an http(s)/other value passes through unchanged."""
    if not isinstance(value, str) or not value.startswith("data:"):
        return value
    try:
        head, b64 = value.split(",", 1)
        content_type = (head[5:].split(";")[0] or "application/octet-stream")
        data = base64.b64decode(b64)
    except Exception:
        return value
    return _upload(data, content_type, "upload" + _UPLOAD_EXT.get(content_type, ".bin"), key) or value


_MEDIA_KEYS = ("start_frame_image", "end_frame_image", "reference_images",
               "reference_videos", "reference_audios")


def _upload_media(payload, key):
    """Replace every local (data: URI) media value in the payload with a hosted URL before we submit.
    Video endpoints take URLs only; image endpoints also accept base64, but hosting keeps the
    submit body small and the two capabilities on one path."""
    if not key:
        return payload
    out = dict(payload)
    for k in _MEDIA_KEYS:
        v = out.get(k)
        if isinstance(v, list):
            out[k] = [_ensure_hosted(x, key) for x in v]
        elif v:
            out[k] = _ensure_hosted(v, key)
    return out


# ------------------------------------------------------------------------------- the async queue
# Submit and poll are split so a caller can submit in one tool call and rejoin the SAME job in a
# later one. `data.urls.get` is absolute + stateless, so it fully identifies the job and no
# server-side state is kept. We return it as BOTH status_url and response_url: one GET answers the
# status and, once complete, carries the outputs — so the client's fal-shaped handle works unchanged.
def queue_submit(endpoint, body, key):
    """Submit one job. Returns {ok, request_id, status_url, response_url} | {ok: False, error, detail}."""
    sub, status, err = supercmo_env._request(
        "POST", f"{BASE}/{endpoint}", body=body, headers=_headers(key))
    if sub is None:
        return {"ok": False, "error": _reason(err) or f"submit failed ({status})",
                "status": status, "detail": (err or "")[:500]}
    d = _data(sub)
    get_url = (d.get("urls") or {}).get("get")
    if not get_url:
        return {"ok": False, "error": "wavespeed: missing result url in submit response",
                "detail": json.dumps(sub)[:500]}
    supercmo_env.dbg(f"wavespeed submit {endpoint} -> id={d.get('id')}")
    return {"ok": True, "request_id": d.get("id"), "status_url": get_url, "response_url": get_url}


def queue_status(status_url, response_url, key):
    """One status check. While the job runs → {ok: True, done: False, state}. On completion →
    {ok: True, done: True, result: <data>}. A network/timeout hiccup → {ok: False, transient: True,
    ...} (keep polling). A real vendor failure → {ok: False, terminal: True, ...}. Short timeout +
    single attempt so one unanswered poll returns fast instead of eating the caller's wait budget."""
    st, code, serr = supercmo_env._request("GET", status_url, headers=_headers(key),
                                           timeout=_STATUS_POLL_TIMEOUT, retries=1)
    if st is None:
        # No status code at all means the network failed; a 5xx is the vendor wobbling; 408 and 429
        # explicitly mean try again. Any other 4xx is the request itself being wrong — a dead or
        # expired handle, a bad key — and retrying one polls forever.
        kind = "transient" if supercmo_env.retryable_status(code) else "terminal"
        return {"ok": False, kind: True, "error": _reason(serr) or f"status check failed ({code})",
                "status": code, "detail": (serr or "")[:500]}
    d = _data(st)
    state = d.get("status")
    if state in _PENDING_STATES:
        return {"ok": True, "done": False, "state": state}
    if state == "completed":
        return {"ok": True, "done": True, "result": d}
    # failed / cancelled / timeout — the vendor is done with this job and will answer the same forever
    return {"ok": False, "terminal": True,
            "error": d.get("error") or f"wavespeed job {state or 'in an unknown state'}",
            "detail": json.dumps(d)[:500]}


def _outputs(result):
    """`data.outputs` as a list of URL strings (the one result shape WaveSpeed uses everywhere)."""
    return [o for o in ((result or {}).get("outputs") or []) if isinstance(o, str) and o]


def _queue_run(endpoint, body, key):
    """Submit + blocking poll to completion (stdlib sleep, `_MAX_POLLS` bound). Used by the
    server-side managed lane, which owns its own call; the BYOK path submits and rejoins instead.
    Returns (result_data, None) | (None, error_dict)."""
    sub = queue_submit(endpoint, body, key)
    if not sub.get("ok"):
        return None, sub
    for _ in range(_MAX_POLLS):
        st = queue_status(sub["status_url"], sub["response_url"], key)
        if not st.get("ok"):
            if st.get("terminal"):
                return None, st
        elif st.get("done"):
            return st["result"], None
        time.sleep(_POLL_INTERVAL)
    supercmo_env.dbg(f"wavespeed queue TIMED OUT after {_MAX_POLLS} polls")
    return None, {"ok": False, "error": "wavespeed queue timed out"}


# ---------------------------------------------------------------------------------------- image
def _build_input(route, payload):
    """The submit body for an image endpoint. `sizes` maps our ratio string to whatever this model
    wants (a ratio string, or FLUX's "1024*1024"); `size_style` names the param it lands in. The
    edit endpoint often accepts fewer params than its text-to-image twin, so when references are
    present `edit_supports` (where declared) is the filter."""
    refs = payload.get("reference_images") or []
    supports = (route.get("edit_supports") if refs else None) or route["supports"]
    p = dict(route.get("defaults", {}))
    p["prompt"] = payload["prompt"]
    aspect = payload.get("aspect_ratio")
    size = route["sizes"].get(aspect) or next(iter(route["sizes"].values()), None)
    if size is not None:
        p["size" if route["size_style"] == "size_wh" else "aspect_ratio"] = size
    res = (payload.get("resolution") or "").lower()   # WaveSpeed tiers are lowercase everywhere
    # A tier this model doesn't bill is dropped, not sent — the model falls back to its own default
    # instead of 422-ing (e.g. Seedream tops out at 2k, so a 4k ask still produces an image).
    if res and (not route.get("resolutions") or res in route["resolutions"]):
        p["resolution"] = res
    if refs:
        p[route.get("ref_param", "images")] = refs[0] if route.get("ref_scalar") else refs
    return {k: v for k, v in p.items() if k in supports}


def _endpoint(route, payload):
    return route["edit_id"] if payload.get("reference_images") else route["id"]


def _images(result):
    return [{"url": u} for u in _outputs(result)]


def image_submit(route, payload, key):
    """Submit an image job. Returns {ok, request_id, status_url, response_url} | {ok: False, ...}."""
    refs = payload.get("reference_images") or []
    if len(refs) > route["max_refs"]:
        return {"ok": False, "error": f"{payload.get('model')} accepts at most {route['max_refs']} "
                f"reference image(s); got {len(refs)}."}
    payload = _upload_media(payload, key)
    return queue_submit(_endpoint(route, payload), _build_input(route, payload), key)


def image_generate(route, payload, key):
    """Blocking image call (submit + poll). The BYOK path uses image_submit/image_status instead;
    this is the entry the server-side managed lane calls. Returns {ok, model, images} | {ok: False}."""
    refs = payload.get("reference_images") or []
    if len(refs) > route["max_refs"]:
        return {"ok": False, "error": f"{payload.get('model')} accepts at most {route['max_refs']} "
                f"reference image(s); got {len(refs)}."}
    payload = _upload_media(payload, key)
    result, err = _queue_run(_endpoint(route, payload), _build_input(route, payload), key)
    if err:
        return err
    images = _images(result)
    if not images:
        return {"ok": False, "error": "no images returned", "detail": json.dumps(result)[:500]}
    return {"ok": True, "model": payload.get("model"), "images": images}


def image_status(status_url, response_url, key):
    """Check a submitted image job. Pending → {ok: True, done: False, state}; completed →
    {ok: True, done: True, images}; else {ok: False, ...}. Model is added by the client."""
    st = queue_status(status_url, response_url, key)
    if not st.get("ok") or not st.get("done"):
        return st
    images = _images(st["result"])
    if not images:
        return {"ok": False, "error": "no images returned", "detail": json.dumps(st["result"])[:500]}
    return {"ok": True, "done": True, "images": images}


def _mask(value):
    if isinstance(value, str) and value.startswith("data:"):
        return f"{value[:32]}...<{len(value)} chars>"
    return value


def image_request_spec(route, payload):
    body = dict(_build_input(route, payload))
    for k in ("images", "image"):
        if isinstance(body.get(k), list):
            body[k] = [_mask(v) for v in body[k]]
        elif body.get(k) is not None:
            body[k] = _mask(body[k])
    return {"method": "POST", "url": f"{BASE}/{_endpoint(route, payload)}",
            "headers": {"Authorization": "Bearer ***", "Content-Type": "application/json"}, "body": body}


# ---------------------------------------------------------------------------------------- video
def _build_video_input(route, payload):
    """The submit body for the resolved video endpoint. The endpoint's `media` map says which tool
    field lands in which WaveSpeed param, and whether that param is a list or a single value —
    declared per endpoint rather than guessed from the name, because WaveSpeed is inconsistent
    (Wan's `videos` is a list, Grok's `video` is scalar)."""
    p = dict(route.get("defaults", {}))
    p["prompt"] = payload["prompt"]
    scalars = set(route.get("media_scalar", ()))
    for kind, param in route.get("media", {}).items():
        val = payload.get(kind)
        if not val:
            continue
        vals = val if isinstance(val, list) else [val]
        p[param] = vals[0] if param in scalars else vals
    if payload.get("aspect_ratio") and route.get("aspects"):
        p["aspect_ratio"] = payload["aspect_ratio"]
    if payload.get("duration") is not None and route.get("durations"):
        p["duration"] = int(payload["duration"])
    if payload.get("resolution") and route.get("resolutions"):
        p["resolution"] = payload["resolution"]
    ap = route.get("audio_param")
    if ap and payload.get("generate_audio") is not None:
        p[ap] = payload["generate_audio"]
    return p


def _video(result):
    out = _outputs(result)
    return {"url": out[0]} if out else None


def video_submit(route, payload, key):
    """Submit a video job without waiting (host local media first). Returns
    {ok, request_id, status_url, response_url} | {ok: False, ...}. The client waits/rejoins."""
    payload = _upload_media(payload, key)
    return queue_submit(route["id"], _build_video_input(route, payload), key)


def video_generate(route, payload, key):
    """Blocking video call (submit + poll). The BYOK path uses video_submit/video_status instead;
    this is the entry the server-side managed lane calls."""
    payload = _upload_media(payload, key)
    result, err = _queue_run(route["id"], _build_video_input(route, payload), key)
    if err:
        return err
    vid = _video(result)
    if not vid:
        return {"ok": False, "error": "no video returned", "detail": json.dumps(result)[:500]}
    return {"ok": True, "model": payload.get("model"), "video": vid,
            "duration": payload.get("duration")}


def video_status(status_url, response_url, key):
    """Check a submitted video job. Pending → {ok: True, done: False, state}; completed →
    {ok: True, done: True, video:{url}, duration}; else {ok: False, ...}. Model is added by the
    client. WaveSpeed reports no duration, so the client's requested value stands."""
    st = queue_status(status_url, response_url, key)
    if not st.get("ok") or not st.get("done"):
        return st
    vid = _video(st["result"])
    if not vid:
        return {"ok": False, "error": "no video returned", "detail": json.dumps(st["result"])[:500]}
    return {"ok": True, "done": True, "video": vid, "duration": None}


def video_request_spec(route, payload):
    body = dict(_build_video_input(route, payload))
    for k, v in list(body.items()):
        if isinstance(v, list):
            body[k] = [_mask(x) for x in v]
        else:
            body[k] = _mask(v)
    return {"method": "POST", "url": f"{BASE}/{route['id']}",
            "headers": {"Authorization": "Bearer ***", "Content-Type": "application/json"}, "body": body}


# --------------------------------------------------------------------------------------- probe
def probe():
    """FREE key check (never a paid generation): ask for a prediction id that cannot exist. A live
    key gets a 4xx that is NOT 401/403; a bad or unfunded key gets 401/403."""
    _r, code, err = supercmo_env._request(
        "GET", f"{BASE}/predictions/supercmo-probe-000000000000/result",
        headers=_headers(os.environ.get(BYOK_ENV) or ""), timeout=15, retries=1)
    if code in (401, 403):
        return {"ok": False, "error": _reason(err) or f"key rejected ({code})",
                "hint": "check WAVESPEED_API_KEY — note a key only activates after the account's first top-up."}
    if code is None:
        return {"ok": False, "error": "could not reach wavespeed.ai", "detail": (err or "")[:200]}
    return {"ok": True}


if __name__ == "__main__":
    # ---- image request specs: ratio-style, size_wh-style, and grok's scalar single-image edit ----
    nbp = {"provider": "wavespeed", "id": "google/nano-banana-pro/text-to-image",
           "edit_id": "google/nano-banana-pro/edit", "max_refs": 14, "size_style": "aspect_ratio",
           "sizes": {"1:1": "1:1", "16:9": "16:9"}, "defaults": {"output_format": "png"},
           "supports": {"prompt", "images", "aspect_ratio", "resolution", "output_format"}}
    spec = image_request_spec(nbp, {"prompt": "x", "aspect_ratio": "16:9", "resolution": "2K"})
    assert spec["url"] == f"{BASE}/google/nano-banana-pro/text-to-image", spec
    assert spec["body"]["aspect_ratio"] == "16:9" and spec["body"]["resolution"] == "2k", spec
    espec = image_request_spec(nbp, {"prompt": "x", "aspect_ratio": "1:1",
                                     "reference_images": ["https://x/a.png"]})
    assert espec["url"].endswith("/edit") and espec["body"]["images"] == ["https://x/a.png"], espec

    flux = {"provider": "wavespeed", "id": "wavespeed-ai/flux-2-pro/text-to-image",
            "edit_id": "wavespeed-ai/flux-2-pro/edit", "max_refs": 3, "size_style": "size_wh",
            "sizes": {"1:1": "1024*1024", "16:9": "1344*768"}, "defaults": {},
            "supports": {"prompt", "images", "size", "seed"}}
    fspec = image_request_spec(flux, {"prompt": "x", "aspect_ratio": "16:9"})
    assert fspec["body"]["size"] == "1344*768" and "aspect_ratio" not in fspec["body"], fspec

    grok = {"provider": "wavespeed", "id": "x-ai/grok-imagine-image/text-to-image",
            "edit_id": "x-ai/grok-imagine-image/edit", "max_refs": 1, "size_style": "aspect_ratio",
            "sizes": {"1:1": "1:1"}, "defaults": {}, "ref_param": "image", "ref_scalar": True,
            "supports": {"prompt", "image", "aspect_ratio", "output_format"}}
    gspec = image_request_spec(grok, {"prompt": "x", "reference_images": ["https://x/a.png"]})
    assert gspec["body"]["image"] == "https://x/a.png", gspec          # scalar, not a list
    over = image_submit(grok, {"prompt": "x", "model": "grok-imagine",
                               "reference_images": ["a", "b"]}, "k")
    assert not over["ok"] and "at most 1" in over["error"], over

    # ---- video request specs: frame pins, list refs, Wan's scalar driving audio ----
    i2v = {"provider": "wavespeed", "id": "bytedance/seedance-2.0/image-to-video",
           "audio_param": "generate_audio", "defaults": {},
           "media": {"start_frame_image": "image", "end_frame_image": "last_image"},
           "media_scalar": ("image", "last_image"),
           "aspects": ["16:9"], "durations": [4, 8], "resolutions": ["720p"]}
    vspec = video_request_spec(i2v, {"prompt": "a cat", "start_frame_image": "http://x/a.png",
                                     "end_frame_image": "http://x/b.png", "aspect_ratio": "16:9",
                                     "duration": 8, "resolution": "720p", "generate_audio": True})
    assert vspec["body"]["image"] == "http://x/a.png" and vspec["body"]["last_image"] == "http://x/b.png", vspec
    assert vspec["body"]["duration"] == 8 and vspec["body"]["generate_audio"] is True, vspec

    t2v = {"provider": "wavespeed", "id": "bytedance/seedance-2.0/text-to-video",
           "audio_param": "generate_audio", "defaults": {},
           "media": {"reference_images": "reference_images", "reference_audios": "reference_audios"},
           "media_scalar": (), "aspects": ["16:9"], "durations": [4], "resolutions": []}
    rspec = video_request_spec(t2v, {"prompt": "x", "reference_images": ["u1", "u2"],
                                     "reference_audios": ["a1"]})
    assert rspec["body"]["reference_images"] == ["u1", "u2"] and rspec["body"]["reference_audios"] == ["a1"], rspec

    wan = {"provider": "wavespeed", "id": "alibaba/wan-2.7/image-to-video", "audio_param": None,
           "defaults": {}, "media": {"start_frame_image": "image", "reference_audios": "audio"},
           "media_scalar": ("image", "audio"), "aspects": [], "durations": [5], "resolutions": ["720p"]}
    wspec = video_request_spec(wan, {"prompt": "x", "start_frame_image": "s.png",
                                     "reference_audios": ["track.mp3"]})
    assert wspec["body"]["audio"] == "track.mp3", wspec                # scalar, not a list

    # ---- queue submit/status split — stub _request so the transitions run without network ----
    _real_request = supercmo_env._request
    _script = []   # queue of (parsed, status, err) tuples, consumed per _request call

    def _stub_request(method, url, body=None, headers=None, timeout=120, retries=None):
        return _script.pop(0)
    supercmo_env._request = _stub_request
    try:
        _script[:] = [({"code": 200, "data": {"id": "p1", "status": "created",
                                              "urls": {"get": "https://api/w/p1/result"}}}, 200, None)]
        sub = queue_submit("bytedance/seedance-2.0/text-to-video", {"prompt": "x"}, "k")
        assert sub["ok"] and sub["request_id"] == "p1", sub
        # one url serves as both, so the client's fal-shaped handle needs no special-casing
        assert sub["status_url"] == sub["response_url"] == "https://api/w/p1/result", sub

        _script[:] = [({"code": 200, "data": {"status": "processing"}}, 200, None)]
        st = queue_status(sub["status_url"], sub["response_url"], "k")
        assert st["ok"] and st["done"] is False and st["state"] == "processing", st

        # completed: status AND outputs arrive together — a single GET, unlike fal's two
        _script[:] = [({"code": 200, "data": {"status": "completed",
                                              "outputs": ["https://cdn/v.mp4"]}}, 200, None)]
        vst = video_status(sub["status_url"], sub["response_url"], "k")
        assert vst["ok"] and vst["done"] and vst["video"]["url"] == "https://cdn/v.mp4", vst

        _script[:] = [({"code": 200, "data": {"status": "completed",
                                              "outputs": ["https://cdn/i.png"]}}, 200, None)]
        ist = image_status(sub["status_url"], sub["response_url"], "k")
        assert ist["ok"] and ist["done"] and ist["images"] == [{"url": "https://cdn/i.png"}], ist

        # a failed job is terminal, and its reason is surfaced rather than a bare state name
        _script[:] = [({"code": 200, "data": {"status": "failed", "error": "content rejected"}}, 200, None)]
        bad = queue_status("u", "u", "k")
        assert not bad["ok"] and bad["terminal"] and bad["error"] == "content rejected", bad

        # a 4xx on poll is terminal (a dead handle); a 5xx is transient (keep waiting)
        _script[:] = [(None, 404, '{"message":"not found"}')]
        assert queue_status("u", "u", "k").get("terminal"), "4xx poll must be terminal"
        _script[:] = [(None, 503, "")]
        assert queue_status("u", "u", "k").get("transient"), "5xx poll must be transient"

        # submit error text comes out of data.error, not the raw body
        _script[:] = [(None, 400, '{"code":400,"data":{"error":"prompt too long"}}')]
        assert queue_submit("x", {}, "k")["error"] == "prompt too long"
    finally:
        supercmo_env._request = _real_request

    # ---- multipart body is well formed (no network) ----
    body, ct = _multipart(b"\x89PNG\r\n", "image/png", "upload.png")
    assert ct.startswith("multipart/form-data; boundary=----supercmo"), ct
    b = ct.split("boundary=")[1]
    assert body.startswith(f"--{b}\r\n".encode()) and body.endswith(f"\r\n--{b}--\r\n".encode()), body
    assert b'name="file"; filename="upload.png"' in body and b"\x89PNG\r\n" in body, body

    print("wavespeed OK:", spec["url"], "|", fspec["body"]["size"], "| queue submit/status split")
