"""Gemini direct adapter — vision. BYOK: GEMINI_API_KEY.

Backs image_analysis / video_analysis: the media rides inline as base64 in the JSON request, so
the standard JSON _request works.
"""
import base64
import json
import os

import supercmo_env

BYOK_ENV = "GEMINI_API_KEY"
KEY_ENABLES = "image · video analysis (vision)"
KEY_SIGNUP = "aistudio.google.com"
_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


def is_available():
    return bool(os.environ.get(BYOK_ENV))


def _url(route):
    return f"{_BASE}/{route['id']}:generateContent"


# ---------------------------------------------------------------------- vision
_DEFAULT_ANALYZE_PROMPT = "Describe this image in detail."


def _usage(parsed):
    """Exact billing drivers for the metered proxy: token counts + the model that actually served
    (modelVersion lets the server self-correct the gemini-flash*-latest alias). Additive — BYOK
    callers ignore it."""
    # thoughtsTokenCount (3.x thinking) is billed at the output rate but reported separately from
    # candidatesTokenCount → count both. cachedContentTokenCount is the cache-hit subset of
    # promptTokenCount, billed at the cheaper cached rate → surface it so the server splits it out.
    um = parsed.get("usageMetadata") or {}
    return {"model_version": parsed.get("modelVersion"),
            "in_tok": um.get("promptTokenCount", 0),
            "cached": um.get("cachedContentTokenCount", 0),
            "out_tok": um.get("candidatesTokenCount", 0) + um.get("thoughtsTokenCount", 0)}


def _resolve_image(image):
    """(mime, base64_data, None) for a data: URI or an http(s) URL; (None, None, error) on failure.
    Gemini's generateContent needs inline image bytes — a URL is fetched here, at call time."""
    image = (image or "").strip()
    if image.startswith("data:"):
        try:
            head, b64 = image.split(",", 1)
            return (head[5:].split(";")[0] or "image/png"), b64, None
        except Exception:
            return None, None, "malformed data URI"
    if image.startswith(("http://", "https://")):
        # Agent-supplied URL fetched server-side → MUST go through the SSRF guard (never the plain
        # _request_raw, which any URL — incl. http://169.254.169.254/… cloud metadata — would reach).
        try:
            data, ctype = supercmo_env.safe_fetch_bytes(image)
        except ValueError as e:
            return None, None, f"could not fetch image url: {e}"
        return (ctype or "image/png").split(";")[0], base64.b64encode(data).decode("ascii"), None
    return None, None, "image must be a data URI or an http(s) URL"


def _build_analyze_body(mime, b64, prompt):
    return {"contents": [{"parts": [
        {"text": prompt or _DEFAULT_ANALYZE_PROMPT},
        {"inline_data": {"mime_type": mime, "data": b64}},
    ]}]}


def analyze_generate(route, payload, key):
    mime, b64, err = _resolve_image(payload.get("image"))
    if err:
        return {"ok": False, "error": f"gemini analyze: {err}"}
    parsed, status, e = supercmo_env._request(
        "POST", _url(route), body=_build_analyze_body(mime, b64, payload.get("prompt")),
        headers={"x-goog-api-key": key})
    if parsed is None:
        return {"ok": False, "error": f"gemini analyze failed ({status})", "detail": (e or "")[:500]}
    try:
        parts = parsed["candidates"][0]["content"]["parts"]
        text = "".join(p.get("text", "") for p in parts).strip()
    except (KeyError, IndexError, TypeError):
        text = None
    if not text:
        return {"ok": False, "error": "gemini analyze: no text in response", "detail": json.dumps(parsed)[:300]}
    return {"ok": True, "model": payload.get("model"), "text": text, "usage": _usage(parsed)}


def analyze_request_spec(route, payload):
    # Mask the image bytes in dry-run (they can be megabytes of base64; a URL isn't fetched here).
    return {"method": "POST", "url": _url(route),
            "headers": {"x-goog-api-key": "***", "Content-Type": "application/json"},
            "body": {"contents": [{"parts": [
                {"text": payload.get("prompt") or _DEFAULT_ANALYZE_PROMPT},
                {"inline_data": {"mime_type": "<image-mime>", "data": "<base64>"}}]}]}}


_DEFAULT_VIDEO_ANALYZE_PROMPT = (
    "Describe this video in detail — subject, setting, key actions, camera work and motion, "
    "pacing, and the gist of any audio.")


def analyze_video_generate(route, payload, key):
    # Same generateContent path as image analysis; Gemini reads an inline video the same way.
    mime, b64, err = _resolve_image(payload.get("video"))
    if err:
        return {"ok": False, "error": f"gemini analyze: {err}"}
    prompt = payload.get("prompt") or _DEFAULT_VIDEO_ANALYZE_PROMPT
    parsed, status, e = supercmo_env._request(
        "POST", _url(route), body=_build_analyze_body(mime, b64, prompt),
        headers={"x-goog-api-key": key})
    if parsed is None:
        return {"ok": False, "error": f"gemini analyze failed ({status})", "detail": (e or "")[:500]}
    try:
        parts = parsed["candidates"][0]["content"]["parts"]
        text = "".join(p.get("text", "") for p in parts).strip()
    except (KeyError, IndexError, TypeError):
        text = None
    if not text:
        return {"ok": False, "error": "gemini analyze: no text in response", "detail": json.dumps(parsed)[:300]}
    return {"ok": True, "model": payload.get("model"), "text": text, "usage": _usage(parsed)}


def analyze_video_request_spec(route, payload):
    return {"method": "POST", "url": _url(route),
            "headers": {"x-goog-api-key": "***", "Content-Type": "application/json"},
            "body": {"contents": [{"parts": [
                {"text": payload.get("prompt") or _DEFAULT_VIDEO_ANALYZE_PROMPT},
                {"inline_data": {"mime_type": "<video-mime>", "data": "<base64>"}}]}]}}
