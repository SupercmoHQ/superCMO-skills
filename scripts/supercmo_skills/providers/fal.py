"""FAL provider — sync image (fal.run) + queued video/tts (queue.fal.run).

Uniform provider contract (mirrors Hermes's providers, minus the registry):
  BYOK_ENV                            env var whose presence means "use me directly"
  is_available()                      True when that key is set
  <cap>_generate(route, payload, key) run a generation; payload = semantic input
  <cap>_request_spec(route, payload)  dry-run shape (key masked)

`route` carries this provider's per-model config (id / edit_id / sizes / supports / queued / …)
from the catalog, so the provider owns its own ids + constraints (e.g. max_refs).

Image is synchronous (one POST to fal.run). Video/tts are long-running, so they use fal's async
queue: submit to queue.fal.run, poll status_url until COMPLETED, then fetch response_url.
"""
import json
import os
import time

import supercmo_env

BASE = "https://fal.run"
QUEUE_BASE = "https://queue.fal.run"
BYOK_ENV = "FAL_KEY"
_POLL_INTERVAL = 3       # seconds between status polls
_MAX_POLLS = 120         # ~6 min ceiling at 3s


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


# ----------------------------------------------------------- async queue (video + tts)
def _queue_run(endpoint, fal_input, key):
    """Submit to fal's async queue, poll to COMPLETED, fetch result.
    Returns (parsed_result, None) | (None, error_dict). Blocking (stdlib sleep, _MAX_POLLS bound)."""
    headers = {"Authorization": f"Key {key}"}
    sub, status, err = supercmo_env._request("POST", f"{QUEUE_BASE}/{endpoint}", body=fal_input, headers=headers)
    if sub is None:
        return None, {"ok": False, "error": f"submit failed ({status})", "detail": (err or "")[:500]}
    status_url, response_url = sub.get("status_url"), sub.get("response_url")
    if not status_url or not response_url:
        return None, {"ok": False, "error": "fal queue: missing status/response url", "detail": json.dumps(sub)[:500]}
    for _ in range(_MAX_POLLS):
        st, code, serr = supercmo_env._request("GET", status_url, headers=headers)
        state = (st or {}).get("status")
        if state == "COMPLETED":
            res, rcode, rerr = supercmo_env._request("GET", response_url, headers=headers)
            if res is None:
                return None, {"ok": False, "error": f"result fetch failed ({rcode})", "detail": (rerr or "")[:500]}
            return res, None
        if state not in ("IN_QUEUE", "IN_PROGRESS"):
            return None, {"ok": False, "error": f"fal queue state: {state}", "detail": json.dumps(st or {})[:500]}
        time.sleep(_POLL_INTERVAL)
    return None, {"ok": False, "error": "fal queue timed out"}


# --------------------------------------------------------------------- video (queue)
def _build_video_input(route, payload):
    p = dict(route.get("defaults", {}))
    p["prompt"] = payload["prompt"]
    aspect = payload.get("aspect_ratio")
    mapped = (route.get("sizes") or {}).get(aspect)
    if mapped:                         # Hermes drops aspect_ratio when the family doesn't
        p["aspect_ratio"] = mapped     # advertise the value — veo3.1 accepts only auto/16:9/9:16 (not 1:1)
    refs = payload.get("reference_images") or []
    if payload.get("image_url"):
        p["image_url"] = payload["image_url"]
    elif refs:
        p["image_url"] = refs[0]          # image-to-video takes a single start frame
    for k in ("duration", "resolution", "generate_audio", "seed"):
        if payload.get(k) is not None:
            p[k] = payload[k]
    unit = route.get("duration_unit")          # veo wants "8s"; the tool passes an int (Hermes parity)
    if unit and p.get("duration") is not None:
        p["duration"] = f"{int(p['duration'])}{unit}"
    return {k: v for k, v in p.items() if k in route["supports"]}


def _video(parsed):
    v = (parsed or {}).get("video")     # veo3.1 result path: result["video"]["url"] (Hermes)
    if isinstance(v, dict) and v.get("url"):
        return {k: v[k] for k in ("url", "content_type", "file_size", "duration") if v.get(k) is not None}
    if isinstance(v, str) and v:        # Hermes also accepts a bare-string video URL
        return {"url": v}
    return None


def video_generate(route, payload, key):
    """Direct fal video call (queued). Returns {ok, model, video:{url}, duration} | {ok: False, ...}."""
    parsed, err = _queue_run(route["id"], _build_video_input(route, payload), key)
    if err:
        return err
    vid = _video(parsed)
    if not vid:
        return {"ok": False, "error": "no video returned", "detail": json.dumps(parsed)[:500]}
    return {"ok": True, "model": payload.get("model"), "video": vid,
            "duration": vid.get("duration") or payload.get("duration")}


def video_request_spec(route, payload):
    return {"method": "POST", "url": f"{QUEUE_BASE}/{route['id']}",
            "headers": {"Authorization": "Key ***", "Content-Type": "application/json"},
            "body": _build_video_input(route, payload)}


# ----------------------------------------------------------------------- tts (queue)
def _build_tts_input(route, payload):
    p = dict(route.get("defaults", {}))
    p["text"] = payload["text"]
    for k in ("voice", "speed", "stability", "similarity_boost"):
        if payload.get(k) is not None:
            p[k] = payload[k]
    return {k: v for k, v in p.items() if k in route["supports"]}


def _audio(parsed):
    a = (parsed or {}).get("audio")
    if isinstance(a, dict) and a.get("url"):
        return {k: a[k] for k in ("url", "content_type", "duration") if a.get(k) is not None}
    return None


def tts_generate(route, payload, key):
    """Direct fal tts call (queued). Returns {ok, model, audio:{url}} | {ok: False, ...}."""
    parsed, err = _queue_run(route["id"], _build_tts_input(route, payload), key)
    if err:
        return err
    aud = _audio(parsed)
    if not aud:
        return {"ok": False, "error": "no audio returned", "detail": json.dumps(parsed)[:500]}
    return {"ok": True, "model": payload.get("model"), "audio": aud}


def tts_request_spec(route, payload):
    return {"method": "POST", "url": f"{QUEUE_BASE}/{route['id']}",
            "headers": {"Authorization": "Key ***", "Content-Type": "application/json"},
            "body": _build_tts_input(route, payload)}


if __name__ == "__main__":
    vroute = {"provider": "fal", "id": "fal-ai/veo3.1/fast/image-to-video", "queued": True,
              "sizes": {"landscape": "16:9"}, "defaults": {"duration": "8"},
              "supports": {"prompt", "image_url", "duration", "aspect_ratio"}}
    vspec = video_request_spec(vroute, {"prompt": "a cat", "model": "veo3.1-fast", "aspect_ratio": "landscape"})
    assert vspec["url"] == f"{QUEUE_BASE}/fal-ai/veo3.1/fast/image-to-video", vspec
    assert vspec["body"]["aspect_ratio"] == "16:9", vspec
    troute = {"provider": "fal", "id": "fal-ai/elevenlabs/tts/eleven-v3", "queued": True,
              "defaults": {"voice": "Aria"}, "supports": {"text", "voice"}}
    tspec = tts_request_spec(troute, {"text": "hi", "model": "elevenlabs-v3"})
    assert tspec["url"] == f"{QUEUE_BASE}/fal-ai/elevenlabs/tts/eleven-v3", tspec
    iroute = {"provider": "fal", "id": "fal-ai/nano-banana", "edit_id": "fal-ai/nano-banana/edit",
              "max_refs": 4, "size_style": "aspect_ratio", "sizes": {"1:1": "1:1"},
              "defaults": {}, "supports": {"prompt", "aspect_ratio"}}
    ispec = image_request_spec(iroute, {"prompt": "x", "aspect_ratio": "1:1"})
    assert ispec["url"].startswith(BASE) and not ispec["url"].startswith(QUEUE_BASE), ispec
    print("fal OK:", vspec["url"], "|", tspec["url"], "|", ispec["url"])
