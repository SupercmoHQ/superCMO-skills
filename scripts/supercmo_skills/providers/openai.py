"""OpenAI direct adapter — tts (Audio Speech API). BYOK: OPENAI_API_KEY.

Faithful stdlib reproduction of Hermes's OpenAI tts provider (tools/tts_tool.py:_generate_openai_tts,
client.audio.speech.create) — same uniform contract as fal. TTS returns raw audio bytes → surfaced as
base64 in the envelope. `response_format` defaults to "mp3", `speed` is clamped to [0.25, 4.0] and only
sent when != 1.0, and each call carries an `x-idempotency-key` header — all matching Hermes.
"""
import base64
import os
import uuid

import supercmo_env

BYOK_ENV = "OPENAI_API_KEY"
_BASE = "https://api.openai.com/v1"

_DEFAULT_TTS_VOICE = "alloy"         # DEFAULT_OPENAI_VOICE
_DEFAULT_TTS_FORMAT = "mp3"          # mp3 unless caller asks for opus (extension-driven in Hermes)


def is_available():
    return bool(os.environ.get(BYOK_ENV))


# ------------------------------------------------------------------------- tts
def _build_tts_input(route, payload):
    p = {"model": route["id"], "input": payload["text"],
         "voice": payload.get("voice") or _DEFAULT_TTS_VOICE,
         "response_format": _DEFAULT_TTS_FORMAT}
    speed = payload.get("speed")
    if speed is not None:
        try:
            speed = float(speed)
        except (TypeError, ValueError):
            speed = None
        # Hermes only sends speed when != 1.0, clamped to the API band [0.25, 4.0].
        if speed is not None and speed != 1.0:
            p["speed"] = max(0.25, min(4.0, speed))
    return p


def tts_generate(route, payload, key):
    try:
        data, ctype, status, err = supercmo_env._request_raw(
            "POST", f"{_BASE}/audio/speech", body=_build_tts_input(route, payload),
            headers={"Authorization": f"Bearer {key}", "x-idempotency-key": str(uuid.uuid4())})
        if data is None:
            return {"ok": False, "error": f"openai tts failed ({status})", "detail": (err or "")[:500]}
        return {"ok": True, "model": payload.get("model"),
                "audio": {"b64": base64.b64encode(data).decode("ascii"),
                          "content_type": ctype or "audio/mpeg"}}
    except Exception as e:  # never raise out of *_generate
        return {"ok": False, "error": "openai tts error", "detail": f"{type(e).__name__}: {e}"[:500]}


def tts_request_spec(route, payload):
    return {"method": "POST", "url": f"{_BASE}/audio/speech",
            "headers": {"Authorization": "Bearer ***", "Content-Type": "application/json",
                        "x-idempotency-key": "***"},
            "body": _build_tts_input(route, payload)}
