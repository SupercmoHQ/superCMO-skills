"""Gemini direct adapter — tts. BYOK: GEMINI_API_KEY.

Gemini TTS (generativelanguage) returns inline base64 PCM audio in the JSON response, so the
standard JSON _request works.
"""
import base64
import io
import json
import os
import re
import wave

import supercmo_env

BYOK_ENV = "GEMINI_API_KEY"
_BASE = "https://generativelanguage.googleapis.com/v1beta/models"


def _pcm_to_wav(pcm, mime):
    """Gemini TTS returns headerless L16 PCM; wrap it in a WAV container so the saved file plays."""
    m = re.search(r"rate=(\d+)", mime or "")
    rate = int(m.group(1)) if m else 24000
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)      # Gemini TTS is mono
        w.setsampwidth(2)      # L16 = 16-bit
        w.setframerate(rate)
        w.writeframes(pcm)
    return buf.getvalue()


def is_available():
    return bool(os.environ.get(BYOK_ENV))


def _build_body(route, payload):
    voice = payload.get("voice") or "Kore"
    return {
        "contents": [{"parts": [{"text": payload["text"]}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": voice}}},
        },
    }


def _url(route):
    return f"{_BASE}/{route['id']}:generateContent"


def tts_generate(route, payload, key):
    parsed, status, err = supercmo_env._request(
        "POST", _url(route), body=_build_body(route, payload), headers={"x-goog-api-key": key})
    if parsed is None:
        return {"ok": False, "error": f"gemini tts failed ({status})", "detail": (err or "")[:500]}
    try:
        part = parsed["candidates"][0]["content"]["parts"][0]["inlineData"]
        mime = part.get("mimeType", "audio/L16")
        if "L16" in mime or "pcm" in mime.lower():
            wav = _pcm_to_wav(base64.b64decode(part["data"]), mime)
            return {"ok": True, "model": payload.get("model"),
                    "audio": {"b64": base64.b64encode(wav).decode("ascii"), "content_type": "audio/wav"}}
        return {"ok": True, "model": payload.get("model"),
                "audio": {"b64": part["data"], "content_type": mime}}
    except (KeyError, IndexError, TypeError):
        return {"ok": False, "error": "gemini tts: no audio in response", "detail": json.dumps(parsed)[:300]}


def tts_request_spec(route, payload):
    return {"method": "POST", "url": _url(route),
            "headers": {"x-goog-api-key": "***", "Content-Type": "application/json"},
            "body": _build_body(route, payload)}


# ---------------------------------------------------------------------- vision
_DEFAULT_ANALYZE_PROMPT = "Describe this image in detail."


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
        data, ctype, status, _err = supercmo_env._request_raw("GET", image)
        if data is None:
            return None, None, f"could not fetch image url ({status})"
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
    return {"ok": True, "model": payload.get("model"), "text": text}


def analyze_request_spec(route, payload):
    # Mask the image bytes in dry-run (they can be megabytes of base64; a URL isn't fetched here).
    return {"method": "POST", "url": _url(route),
            "headers": {"x-goog-api-key": "***", "Content-Type": "application/json"},
            "body": {"contents": [{"parts": [
                {"text": payload.get("prompt") or _DEFAULT_ANALYZE_PROMPT},
                {"inline_data": {"mime_type": "<image-mime>", "data": "<base64>"}}]}]}}
