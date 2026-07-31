"""FAL provider — sync image (fal.run) + queued video (queue.fal.run).

Uniform provider contract:
  BYOK_ENV                            env var whose presence means "use me directly"
  is_available()                      True when that key is set
  <cap>_generate(route, payload, key) run a generation; payload = semantic input
  <cap>_request_spec(route, payload)  dry-run shape (key masked)

`route` carries this provider's per-model config (id / edit_id / sizes / supports / queued / …)
from the catalog, so the provider owns its own ids + constraints (e.g. max_refs).

Image is synchronous (one POST to fal.run). Video is long-running, so it uses fal's async
queue: submit to queue.fal.run, poll status_url until COMPLETED, then fetch response_url.
"""
import base64
import json
import os
import time

import supercmo_env

BASE = "https://fal.run"
QUEUE_BASE = "https://queue.fal.run"
BYOK_ENV = "FAL_KEY"
KEY_ENABLES = "image · video  (broadest — recommended starter)"
KEY_SIGNUP = "fal.ai"
_POLL_INTERVAL = 3       # seconds between status polls
_MAX_POLLS = 150         # ceiling ≈ 450s sleep + per-poll network (~500-520s wall clock), kept UNDER the
                         # MCP client's 600s per-call timeout so the tool returns its own clean "timed
                         # out" instead of being hard-killed by the caller. (Per-poll network is why the
                         # earlier 180 blew past 600s.) Slower jobs are handed back as a pending
                         # job handle and rejoined via job_status.
_UPLOAD_INITIATE = "https://rest.fal.ai/storage/upload/initiate"
_UPLOAD_EXT = {"image/jpeg": ".jpg", "image/jpg": ".jpg", "image/png": ".png", "image/webp": ".webp",
               "video/mp4": ".mp4", "video/quicktime": ".mov", "video/webm": ".webm",
               "audio/mpeg": ".mp3", "audio/mp3": ".mp3", "audio/wav": ".wav"}


def _upload_to_fal(data, content_type, file_name, key):
    """Upload bytes to fal storage → hosted file_url (or None on failure). fal's two-step flow:
    POST initiate → {upload_url, file_url}; PUT the raw bytes to upload_url. This is fal's recommended
    input path — smaller requests, and some backends (e.g. Kling) need a real URL, not a data: URI."""
    init, _status, _err = supercmo_env._request(
        "POST", _UPLOAD_INITIATE, body={"file_name": file_name, "content_type": content_type},
        headers={"Authorization": f"Key {key}", "Accept": "application/json"})
    if not init or not init.get("upload_url") or not init.get("file_url"):
        return None
    _data, _ct, status, _err = supercmo_env._request_raw(
        "PUT", init["upload_url"], raw_body=data, content_type=content_type, timeout=120, retries=1)
    if status not in (200, 201, 204):
        return None
    return init["file_url"]


def _ensure_hosted(value, key):
    """A local data: URI → uploaded fal URL; an http(s)/other value passes through unchanged."""
    if not isinstance(value, str) or not value.startswith("data:"):
        return value
    try:
        head, b64 = value.split(",", 1)
        content_type = (head[5:].split(";")[0] or "application/octet-stream")
        data = base64.b64decode(b64)
    except Exception:
        return value
    return _upload_to_fal(data, content_type, "upload" + _UPLOAD_EXT.get(content_type, ".bin"), key) or value


_VIDEO_MEDIA_KEYS = ("start_frame_image", "end_frame_image", "reference_images",
                     "reference_videos", "reference_audios")


def _upload_media(payload, key):
    """Replace every local (data: URI) media value in the payload with a fal-hosted URL before we
    submit — fal's recommended path (and required by models that reject data: URIs)."""
    if not key:
        return payload
    out = dict(payload)
    for k in _VIDEO_MEDIA_KEYS:
        v = out.get(k)
        if isinstance(v, list):
            out[k] = [_ensure_hosted(x, key) for x in v]
        elif v:
            out[k] = _ensure_hosted(v, key)
    return out


def is_available():
    return bool(os.environ.get(BYOK_ENV))


# --------------------------------------------------------------------- image (sync)
def _build_input(route, payload):
    p = dict(route.get("defaults", {}))
    p["prompt"] = payload["prompt"]
    aspect = payload.get("aspect_ratio")
    size = route["sizes"].get(aspect) or next(iter(route["sizes"].values()))
    if route["size_style"] == "aspect_ratio":
        p["aspect_ratio"] = size
    else:
        p["image_size"] = size
    res = payload.get("resolution")
    if res:                                    # match the route's tested casing (nano "1K" / grok "1k")
        d = (route.get("defaults") or {}).get("resolution") or ""
        p["resolution"] = res.upper() if d and d[-1] == "K" else res.lower()
    refs = payload.get("reference_images") or []
    if refs:
        p["image_urls"] = refs
    return {k: v for k, v in p.items() if k in route["supports"]}


def _endpoint(route, payload):
    return route["edit_id"] if payload.get("reference_images") else route["id"]


def _images(parsed):
    out = []
    for img in (parsed or {}).get("images", []) or []:
        if isinstance(img, dict) and img.get("url"):
            out.append({k: img[k] for k in ("url", "width", "height", "content_type") if img.get(k) is not None})
    return out


def image_generate(route, payload, key):
    """Direct fal image call (sync). Returns {ok, model, images, seed} | {ok: False, ...}."""
    refs = payload.get("reference_images") or []
    if len(refs) > route["max_refs"]:
        return {"ok": False, "error": f"{payload.get('model')} accepts at most {route['max_refs']} reference image(s); got {len(refs)}."}
    fal_input = _build_input(route, payload)
    parsed, status, err = supercmo_env._request(
        "POST", f"{BASE}/{_endpoint(route, payload)}", body=fal_input, headers={"Authorization": f"Key {key}"})
    if parsed is None:
        return {"ok": False, "error": f"image request failed ({status})", "detail": (err or "")[:500]}
    images = _images(parsed)
    if not images:
        return {"ok": False, "error": "no images returned", "detail": json.dumps(parsed)[:500]}
    return {"ok": True, "model": payload.get("model"), "images": images, "seed": parsed.get("seed")}


def image_submit(route, payload, key):
    """Submit a fal image job on the async queue (same model id, queued so a slow model / 4k / large
    batch can outrun one call and be rejoined). Returns {ok, request_id, status_url, response_url} |
    {ok: False, ...}. Fast images still complete on the first poll."""
    refs = payload.get("reference_images") or []
    if len(refs) > route["max_refs"]:
        return {"ok": False, "error": f"{payload.get('model')} accepts at most {route['max_refs']} reference image(s); got {len(refs)}."}
    return queue_submit(_endpoint(route, payload), _build_input(route, payload), key)


def image_status(status_url, response_url, key):
    """Check a submitted image job. Pending → {ok: True, done: False, state}; completed →
    {ok: True, done: True, images, seed}; else {ok: False, ...}. Model is added by the client."""
    st = queue_status(status_url, response_url, key)
    if not st.get("ok") or not st.get("done"):
        return st
    images = _images(st["result"])
    if not images:
        return {"ok": False, "error": "no images returned", "detail": json.dumps(st["result"])[:500]}
    return {"ok": True, "done": True, "images": images, "seed": st["result"].get("seed")}


def _mask(value):
    if isinstance(value, str) and value.startswith("data:"):
        return f"{value[:32]}...<{len(value)} chars>"
    return value


def image_request_spec(route, payload):
    body = dict(_build_input(route, payload))
    if isinstance(body.get("image_urls"), list):
        body["image_urls"] = [_mask(v) for v in body["image_urls"]]
    return {"method": "POST", "url": f"{BASE}/{_endpoint(route, payload)}",
            "headers": {"Authorization": "Key ***", "Content-Type": "application/json"}, "body": body}


# ----------------------------------------------------------------- async queue (video)
# Submit and poll are split so a caller can submit in one tool call and rejoin the SAME job in a
# later call (the fal status/response URLs are absolute + stateless — they fully identify the job,
# so no server-side state is kept). The client owns the wait budget + rejoin; here we only do the
# two fal HTTP steps. `_queue_run` (submit + blocking loop) is retained for tests / the sync path.
_PENDING_STATES = ("IN_QUEUE", "IN_PROGRESS")
_STATUS_POLL_TIMEOUT = 15   # per status poll: short + single attempt, so one unanswered poll can't
                            # freeze the caller's wait budget (the caller paces its own retry loop)


def queue_submit(endpoint, fal_input, key):
    """Submit one job to fal's async queue. Returns
    {ok, request_id, status_url, response_url} | {ok: False, error, detail}."""
    sub, status, err = supercmo_env._request(
        "POST", f"{QUEUE_BASE}/{endpoint}", body=fal_input, headers={"Authorization": f"Key {key}"})
    if sub is None:
        return {"ok": False, "error": f"submit failed ({status})", "detail": (err or "")[:500]}
    status_url, response_url = sub.get("status_url"), sub.get("response_url")
    if not status_url or not response_url:
        return {"ok": False, "error": "fal queue: missing status/response url", "detail": json.dumps(sub)[:500]}
    supercmo_env.dbg(f"queue submit {endpoint} -> request_id={sub.get('request_id')}")
    return {"ok": True, "request_id": sub.get("request_id"),
            "status_url": status_url, "response_url": response_url}


def queue_status(status_url, response_url, key):
    """One status check on a submitted job. While the job runs → {ok: True, done: False, state}.
    On completion → {ok: True, done: True, result: <parsed>}. A network/timeout hiccup →
    {ok: False, transient: True, ...} (the caller should keep polling, not give up). A real vendor
    failure state → {ok: False, terminal: True, ...}. Short timeout + single attempt: one unanswered
    poll returns fast instead of freezing the caller's wait budget."""
    headers = {"Authorization": f"Key {key}"}
    st, code, serr = supercmo_env._request("GET", status_url, headers=headers,
                                           timeout=_STATUS_POLL_TIMEOUT, retries=1)
    if st is None:                                            # unreachable / slow / timed out → retry
        return {"ok": False, "transient": True, "error": f"status check failed ({code})",
                "detail": (serr or "")[:500]}
    state = st.get("status")
    if state in _PENDING_STATES:
        return {"ok": True, "done": False, "state": state}
    if state == "COMPLETED":
        res, rcode, rerr = supercmo_env._request("GET", response_url, headers=headers,
                                                 timeout=_STATUS_POLL_TIMEOUT, retries=1)
        if res is None:                                      # result not fetched yet → retry
            return {"ok": False, "transient": True, "error": f"result fetch failed ({rcode})",
                    "detail": (rerr or "")[:500]}
        return {"ok": True, "done": True, "result": res}
    return {"ok": False, "terminal": True, "error": f"fal queue state: {state}",
            "detail": json.dumps(st)[:500]}


def _queue_run(endpoint, fal_input, key):
    """Submit + blocking poll to COMPLETED (stdlib sleep, `_MAX_POLLS` bound). Retained for the sync
    path and tests. Returns (parsed_result, None) | (None, error_dict)."""
    sub = queue_submit(endpoint, fal_input, key)
    if not sub.get("ok"):
        return None, sub
    t0 = time.time()
    for _ in range(_MAX_POLLS):
        st = queue_status(sub["status_url"], sub["response_url"], key)
        if not st.get("ok"):
            return None, st
        if st.get("done"):
            return st["result"], None
        time.sleep(_POLL_INTERVAL)
    supercmo_env.dbg(f"queue TIMED OUT after {time.time() - t0:.0f}s / {_MAX_POLLS} polls")
    return None, {"ok": False, "error": "fal queue timed out"}


# --------------------------------------------------------------------- video (queue)
# The client resolves which endpoint to hit and hands us a route carrying that endpoint's `id`, its
# `media` map (tool field -> fal param), and its aspect/duration/resolution value sets. We only emit
# params this endpoint accepts, so there's no cross-mode leakage to 422 on.
def _build_video_input(route, payload):
    """Build the fal input from the resolved endpoint. Media map by fal-name convention: a `*_urls`
    param takes a list, a `*_url` param a single value; duration renders with the model's unit (veo `"8s"`)."""
    p = dict(route.get("defaults", {}))
    p["prompt"] = payload["prompt"]
    elements = []                                             # Kling: images + videos merge into one list
    for kind, fal_param in route.get("media", {}).items():
        val = payload.get(kind)
        if not val:
            continue
        vals = val if isinstance(val, list) else [val]
        if fal_param == "elements":
            # Kling elements: a video element is {video_url}; an image element requires BOTH
            # frontal_image_url AND a non-empty reference_image_urls — so mirror the frame into the refs.
            elements += ([{"video_url": u} for u in vals] if kind == "reference_videos"
                         else [{"frontal_image_url": u, "reference_image_urls": [u]} for u in vals])
        elif fal_param.endswith("_urls"):                     # list param
            p[fal_param] = vals
        else:                                                 # single-value param
            p[fal_param] = vals[0]
    if elements:
        p["elements"] = elements
    if payload.get("aspect_ratio") and route.get("aspects"):
        p["aspect_ratio"] = payload["aspect_ratio"]
    if payload.get("duration") is not None and route.get("durations"):
        unit = route.get("duration_unit")
        p["duration"] = f"{int(payload['duration'])}{unit}" if unit else payload["duration"]
    if payload.get("resolution") and route.get("resolutions"):
        p["resolution"] = payload["resolution"]
    ap = route.get("audio_param")
    if ap and payload.get("generate_audio") is not None:
        p[ap] = payload["generate_audio"]
    return p


def _video(parsed):
    v = (parsed or {}).get("video")     # veo3.1 result path: result["video"]["url"]
    if isinstance(v, dict) and v.get("url"):
        return {k: v[k] for k in ("url", "content_type", "file_size", "duration") if v.get(k) is not None}
    if isinstance(v, str) and v:        # a bare-string video URL is also accepted
        return {"url": v}
    return None


def video_generate(route, payload, key):
    """Direct fal video call (queued, blocking). Returns {ok, model, video:{url}, duration} | {ok: False, ...}."""
    payload = _upload_media(payload, key)   # local files → fal-hosted URLs (fal's recommended input path)
    parsed, err = _queue_run(route["id"], _build_video_input(route, payload), key)
    if err:
        return err
    vid = _video(parsed)
    if not vid:
        return {"ok": False, "error": "no video returned", "detail": json.dumps(parsed)[:500]}
    return {"ok": True, "model": payload.get("model"), "video": vid,
            "duration": vid.get("duration") or payload.get("duration")}


def video_submit(route, payload, key):
    """Submit a fal video job without waiting (host local media first). Returns
    {ok, request_id, status_url, response_url} | {ok: False, ...}. The client waits/rejoins."""
    payload = _upload_media(payload, key)   # local files → fal-hosted URLs (fal's recommended input path)
    return queue_submit(route["id"], _build_video_input(route, payload), key)


def video_status(status_url, response_url, key):
    """Check a submitted video job. Pending → {ok: True, done: False, state}; completed →
    {ok: True, done: True, video:{url}, duration}; else {ok: False, ...}. Model is added by the client."""
    st = queue_status(status_url, response_url, key)
    if not st.get("ok") or not st.get("done"):
        return st
    vid = _video(st["result"])
    if not vid:
        return {"ok": False, "error": "no video returned", "detail": json.dumps(st["result"])[:500]}
    return {"ok": True, "done": True, "video": vid, "duration": vid.get("duration")}


def video_request_spec(route, payload):
    return {"method": "POST", "url": f"{QUEUE_BASE}/{route['id']}",
            "headers": {"Authorization": "Key ***", "Content-Type": "application/json"},
            "body": _build_video_input(route, payload)}


if __name__ == "__main__":
    # resolved veo first-last-frame endpoint: scalar frame params, "8s" duration
    flf = {"provider": "fal", "id": "fal-ai/veo3.1/first-last-frame-to-video", "duration_unit": "s",
           "defaults": {}, "audio_param": "generate_audio",
           "media": {"start_frame_image": "first_frame_url", "end_frame_image": "last_frame_url"},
           "aspects": ["16:9"], "durations": [4, 6, 8], "resolutions": ["720p"]}
    vspec = video_request_spec(flf, {"prompt": "a cat", "start_frame_image": "http://x/a.png",
                                     "end_frame_image": "http://x/b.png", "aspect_ratio": "16:9", "duration": 8})
    assert vspec["url"].endswith("/first-last-frame-to-video"), vspec
    assert vspec["body"]["first_frame_url"] == "http://x/a.png" and vspec["body"]["last_frame_url"] == "http://x/b.png", vspec
    assert vspec["body"]["duration"] == "8s" and vspec["body"]["aspect_ratio"] == "16:9", vspec
    # resolved seedance reference-to-video endpoint: list `*_urls` params
    r2v = {"provider": "fal", "id": "bytedance/seedance-2.0/reference-to-video", "duration_unit": None,
           "defaults": {}, "audio_param": "generate_audio",
           "media": {"reference_images": "image_urls", "reference_audios": "audio_urls"},
           "aspects": [], "durations": [4], "resolutions": []}
    rspec = video_request_spec(r2v, {"prompt": "x", "reference_images": ["u1", "u2"], "reference_audios": ["a1"]})
    assert rspec["body"]["image_urls"] == ["u1", "u2"] and rspec["body"]["audio_urls"] == ["a1"], rspec
    iroute = {"provider": "fal", "id": "fal-ai/nano-banana", "edit_id": "fal-ai/nano-banana/edit",
              "max_refs": 4, "size_style": "aspect_ratio", "sizes": {"1:1": "1:1"},
              "defaults": {}, "supports": {"prompt", "aspect_ratio"}}
    ispec = image_request_spec(iroute, {"prompt": "x", "aspect_ratio": "1:1"})
    assert ispec["url"].startswith(BASE) and not ispec["url"].startswith(QUEUE_BASE), ispec

    # queue submit/status split — stub _request so the transitions are exercised without network.
    _real_request = supercmo_env._request
    _script = []  # queue of (parsed, status, err) tuples, consumed per _request call

    def _stub_request(method, url, body=None, headers=None, timeout=120, retries=None):
        return _script.pop(0)
    supercmo_env._request = _stub_request
    try:
        # submit returns the two absolute urls
        _script[:] = [({"request_id": "r1", "status_url": "https://q/status", "response_url": "https://q/"}, 200, None)]
        sub = queue_submit("bytedance/seedance-2.0/text-to-video", {"prompt": "x"}, "k")
        assert sub["ok"] and sub["status_url"] == "https://q/status" and sub["response_url"] == "https://q/", sub
        # pending status → done:False, no result fetch
        _script[:] = [({"status": "IN_PROGRESS"}, 200, None)]
        st = queue_status(sub["status_url"], sub["response_url"], "k")
        assert st["ok"] and st["done"] is False and st["state"] == "IN_PROGRESS", st
        # completed status → second _request fetches the result
        _script[:] = [({"status": "COMPLETED"}, 200, None),
                      ({"video": {"url": "https://cdn/v.mp4", "duration": 8}}, 200, None)]
        vst = video_status(sub["status_url"], sub["response_url"], "k")
        assert vst["ok"] and vst["done"] and vst["video"]["url"] == "https://cdn/v.mp4" and vst["duration"] == 8, vst
        # image completed → images list parsed (image is queued too)
        _script[:] = [({"status": "COMPLETED"}, 200, None),
                      ({"images": [{"url": "https://cdn/i.png"}], "seed": 7}, 200, None)]
        ist = image_status(sub["status_url"], sub["response_url"], "k")
        assert ist["ok"] and ist["done"] and ist["images"][0]["url"] == "https://cdn/i.png" and ist["seed"] == 7, ist
        # missing urls on submit → actionable error
        _script[:] = [({"request_id": "r2"}, 200, None)]
        bad = queue_submit("x", {"prompt": "y"}, "k")
        assert not bad["ok"] and "missing status/response url" in bad["error"], bad
    finally:
        supercmo_env._request = _real_request

    print("fal OK:", vspec["url"], "|", ispec["url"], "| queue submit/status split")
