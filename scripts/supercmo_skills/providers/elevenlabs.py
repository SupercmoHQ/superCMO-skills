"""ElevenLabs direct adapter — tts. BYOK: ELEVENLABS_API_KEY.

Voice names map to public ElevenLabs voice ids; a raw voice id is also accepted. Returns raw
audio bytes → surfaced as base64 in the envelope.
"""
import base64
import os

import supercmo_env

BYOK_ENV = "ELEVENLABS_API_KEY"
_BASE = "https://api.elevenlabs.io/v1"
_VOICES = {  # name -> public ElevenLabs voice_id
    "Aria": "9BWtsMINqrJLrRacOk9x", "Rachel": "21m00Tcm4TlvDq8ikWAM",
    "Roger": "CwhRBWXzGAHq8TQ4Fs17", "Sarah": "EXAVITQu4vr4xnSDxMaL",
}
_DEFAULT_VOICE_ID = _VOICES["Rachel"]


def is_available():
    return bool(os.environ.get(BYOK_ENV))


def _voice_id(payload):
    v = payload.get("voice")
    return (_VOICES.get(v, v) if v else _DEFAULT_VOICE_ID)   # accept a known name or a raw id


def _build_body(route, payload):
    body = {"text": payload["text"], "model_id": route["id"]}
    vs = {}
    if payload.get("stability") is not None:
        vs["stability"] = payload["stability"]
    if payload.get("similarity_boost") is not None:
        vs["similarity_boost"] = payload["similarity_boost"]
    if vs:
        body["voice_settings"] = vs
    return body


def tts_generate(route, payload, key):
    data, ctype, status, err = supercmo_env._request_raw(
        "POST", f"{_BASE}/text-to-speech/{_voice_id(payload)}", body=_build_body(route, payload),
        headers={"xi-api-key": key, "Accept": "audio/mpeg"})
    if data is None:
        return {"ok": False, "error": f"elevenlabs tts failed ({status})", "detail": (err or "")[:500]}
    return {"ok": True, "model": payload.get("model"),
            "audio": {"b64": base64.b64encode(data).decode("ascii"), "content_type": ctype or "audio/mpeg"}}


def tts_request_spec(route, payload):
    return {"method": "POST", "url": f"{_BASE}/text-to-speech/{_voice_id(payload)}",
            "headers": {"xi-api-key": "***", "Content-Type": "application/json", "Accept": "audio/mpeg"},
            "body": _build_body(route, payload)}
