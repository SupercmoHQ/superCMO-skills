"""xAI direct adapter — video (/v1/videos async submit+poll). BYOK: XAI_API_KEY (Bearer).
Faithful to Hermes's xAI video plugin (plugins/video_gen/xai): same endpoints, body fields,
submit→poll loop, and result extraction. Video result is read from body["video"]["url"] — the
field Hermes reads (video_gen/xai L447-448). We only do the XAI_API_KEY path (Bearer).
"""
import json
import os
import time
import uuid

import supercmo_env

BYOK_ENV = "XAI_API_KEY"
_BASE = "https://api.x.ai/v1"
_POLL_INTERVAL = 3
_MAX_POLLS = 120

# Hermes maps the API's aspect ratios from a fixed set (video_gen/xai VALID_ASPECT_RATIOS).
# Our payload carries the semantic alias (square/landscape/portrait); translate to xAI's form.
_ASPECT = {"square": "1:1", "landscape": "16:9", "portrait": "9:16"}
_DEFAULT_RESOLUTION = "720p"      # video_gen/xai DEFAULT_RESOLUTION
# Hermes video terminal statuses (video_gen/xai _poll L234-237): done | failed/error/expired/cancelled.
_DONE = "done"
_FAILED = {"failed", "error", "expired", "cancelled"}


def is_available():
    return bool(os.environ.get(BYOK_ENV))


def _headers(key):
    return {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}


# ----------------------------------------------------------------------- video
def _build_video_input(route, payload):
    # Hermes video_gen/xai submit body (L405-415): {model, prompt, duration, aspect_ratio,
    # resolution}, plus image:{url} for image-to-video, plus reference_images:[{url}].
    # Hermes routes image-to-video to grok-imagine-video-1.5-preview, text-to-video to
    # grok-imagine-video (_resolve_model_for_modality video_gen/xai L168-187).
    has_image = bool(payload.get("image_url") or (payload.get("reference_images") or []))
    model_id = route.get("i2v_id") if (has_image and route.get("i2v_id")) else route["id"]
    p = {"model": model_id, "prompt": payload["prompt"]}
    if payload.get("duration") is not None:
        p["duration"] = payload["duration"]
    aspect = _ASPECT.get(payload.get("aspect_ratio"))
    if aspect:
        p["aspect_ratio"] = aspect
    p["resolution"] = payload.get("resolution") or _DEFAULT_RESOLUTION
    refs = payload.get("reference_images") or []
    if payload.get("image_url"):
        p["image"] = {"url": payload["image_url"]}
    elif refs:
        p["reference_images"] = [{"url": r} for r in refs]
    return p


def video_generate(route, payload, key):
    headers = _headers(key)
    body = _build_video_input(route, payload)
    # Submit — Hermes sends a per-request x-idempotency-key (video_gen/xai _submit L201).
    sub, status, err = supercmo_env._request(
        "POST", f"{_BASE}/videos/generations", body=body,
        headers={**headers, "x-idempotency-key": str(uuid.uuid4())})
    if sub is None:
        return {"ok": False, "error": f"xai video submit failed ({status})", "detail": (err or "")[:500]}
    rid = sub.get("request_id")              # Hermes reads request_id only (_submit L207).
    if not rid:
        return {"ok": False, "error": "xai video: no request_id", "detail": json.dumps(sub)[:300]}
    # Poll GET /videos/{request_id} (Hermes _poll L225) until terminal status.
    for _ in range(_MAX_POLLS):
        b, code, perr = supercmo_env._request("GET", f"{_BASE}/videos/{rid}", headers=headers)
        st = ((b or {}).get("status") or "").lower()
        if st == _DONE:
            video = (b or {}).get("video") or {}     # Hermes: body["video"]["url"] (L447-448).
            url = video.get("url")
            if not url:
                return {"ok": False, "error": "xai video: completed without a video URL",
                        "detail": json.dumps(b)[:300]}
            return {"ok": True, "model": (b or {}).get("model") or payload.get("model"),
                    "video": {"url": url},
                    "duration": video.get("duration") or payload.get("duration")}
        if st in _FAILED:
            return {"ok": False, "error": f"xai video {st}", "detail": json.dumps(b)[:300]}
        time.sleep(_POLL_INTERVAL)
    return {"ok": False, "error": "xai video timed out"}


def video_request_spec(route, payload):
    return {"method": "POST", "url": f"{_BASE}/videos/generations",
            "headers": {"Authorization": "Bearer ***", "Content-Type": "application/json",
                        "x-idempotency-key": "***"},
            "body": _build_video_input(route, payload)}
