"""ElevenLabs direct adapter — audio. BYOK: ELEVENLABS_API_KEY.

The vendor takes a voice id in the URL path, so `voice` is always an id the caller got from
list_voices — there is no name lookup and no fallback voice. Returns raw audio bytes → surfaced as
base64 in the envelope.
"""
import base64
import os
import urllib.parse

import supercmo_env

BYOK_ENV = "ELEVENLABS_API_KEY"
KEY_ENABLES = "speech / voiceover  (the only audio provider)"
KEY_SIGNUP = "elevenlabs.io"
_BASE = "https://api.elevenlabs.io/v1"
_BASE_V2 = "https://api.elevenlabs.io/v2"

# The API takes one `output_format` string encoding container + sample rate; the tool asks for a
# container, so pair each with that container's best published rate.
_OUTPUT_FORMAT = {"mp3": "mp3_44100_128", "wav": "wav_44100",
                  "pcm": "pcm_44100", "opus": "opus_48000_128"}
_DEFAULT_FORMAT = "mp3"
_CONTENT_TYPE = {"mp3": "audio/mpeg", "wav": "audio/wav",
                 "pcm": "audio/pcm", "opus": "audio/opus"}

# voice_settings sub-fields: [0,1] floats, except speed (a rate multiplier).
_VOICE_SETTINGS = ("stability", "similarity_boost", "style", "speed")


def is_available():
    return bool(os.environ.get(BYOK_ENV))


def probe():
    """Free key-validity check (no paid call): GET /v1/voices. Returns a short status string, or
    None when no key is set. A scoped key that's valid but lacks voices_read reads as such — saying
    "invalid" would send the user to regenerate a key that is actually fine."""
    key = os.environ.get(BYOK_ENV)
    if not key:
        return None
    parsed, status, err = supercmo_env._request("GET", f"{_BASE}/voices", headers={"xi-api-key": key})
    if parsed is not None:
        return "reachable"
    if "voices_read" in (err or ""):
        return "valid, but missing the voices_read permission (voice discovery will be empty)"
    return f"unreachable (HTTP {status})"


def _unresolved_voice(payload):
    """The `voice` value when it isn't id-shaped, else None. The id goes in the URL path, so a name
    would 400 only after the request is already out — catch it before spending.""" 
    v = payload.get("voice")
    if not v or (len(v) >= 20 and v.isalnum()):
        return None
    return v


def _fmt(payload):
    return payload.get("format") or _DEFAULT_FORMAT


def _build_body(route, payload):
    body = {"text": payload["text"], "model_id": route["id"]}
    vs = {k: payload[k] for k in _VOICE_SETTINGS
          if payload.get(k) is not None and k in route["supports"]}
    if vs:
        body["voice_settings"] = vs
    return body


def _url(payload):
    fmt = _fmt(payload)
    return (f"{_BASE}/text-to-speech/{payload['voice']}"
            f"?output_format={_OUTPUT_FORMAT.get(fmt, _OUTPUT_FORMAT[_DEFAULT_FORMAT])}")


def audio_validate(payload):
    """Input errors worth catching before a request goes out; None when the payload is fine."""
    bad = _unresolved_voice(payload)
    if bad:
        return {"ok": False, "error": f"not a voice id: {bad}",
                "hint": "pass the `voice_id` of a row from list_voices, not a display name."}
    return None


def audio_generate(route, payload, key):
    err = audio_validate(payload)
    if err:
        return err
    fmt = _fmt(payload)
    data, ctype, status, err = supercmo_env._request_raw(
        "POST", _url(payload), body=_build_body(route, payload), headers={"xi-api-key": key})
    if data is None:
        return {"ok": False, "error": f"elevenlabs speech failed ({status})", "detail": (err or "")[:500]}
    return {"ok": True, "model": payload.get("model"),
            "audio": {"b64": base64.b64encode(data).decode("ascii"),
                      "content_type": _CONTENT_TYPE.get(fmt) or ctype or "audio/mpeg"}}


def audio_request_spec(route, payload):
    return {"method": "POST", "url": _url(payload),
            "headers": {"xi-api-key": "***", "Content-Type": "application/json"},
            "body": _build_body(route, payload)}


# Vendor keys are permission-scoped: a key minted with only text-to-speech rights returns 401
# `voices_read` on every voice endpoint. That is a key the user must widen, so the reason has to
# reach them instead of collapsing into "lookup failed".
VOICES_SCOPE = "voices_read"

# The label keys ElevenLabs populates on its own curated voices. A voice the user cloned may carry
# none of them, so a row missing the key being filtered on is kept rather than dropped — otherwise
# someone's own voice vanishes the moment anyone filters.
_LABEL_KEYS = ("gender", "accent", "age", "use_case", "language", "descriptive")


def _voice_row(v):
    """Flatten one API voice into the shape the tool returns (labels hoisted to the top level)."""
    labels = v.get("labels") if isinstance(v.get("labels"), dict) else {}
    row = {"voice_id": v["voice_id"], "name": v.get("name")}
    for k in _LABEL_KEYS:
        if labels.get(k):
            row[k] = labels[k]
    if v.get("category"):
        row["category"] = v["category"]
    if v.get("description"):
        row["description"] = str(v["description"])[:160]
    if v.get("preview_url"):
        row["preview_url"] = v["preview_url"]
    return row


def list_voices(key, search=None, limit=8, **filters):
    """(voices, problem) — the voices saved in this account, newest-relevant first, each with its
    labels and a `preview_url` to audition. `search` is passed to the vendor; the label filters are
    applied here because the account endpoint does not accept them.

    Returns None plus a short, actionable reason when the list cannot be read."""
    q = {"page_size": 100}
    if search:
        q["search"] = search
    url = f"{_BASE_V2}/voices?" + urllib.parse.urlencode(q)
    parsed, status, err = supercmo_env._request("GET", url, headers={"xi-api-key": key}, timeout=20)
    if parsed is None:
        if VOICES_SCOPE in (err or ""):
            return None, (f"this key cannot list voices — it lacks the `{VOICES_SCOPE}` permission. "
                          "Add that permission to the key in the ElevenLabs dashboard, or supply a "
                          "voice_id directly.")
        if status in (401, 403):
            return None, ("the provider rejected this key when listing voices — check it is valid "
                          "and may read voices.")
        return None, (f"could not reach the provider to list voices (HTTP {status}) — retry, or "
                      "supply a voice_id directly.")
    if not isinstance(parsed.get("voices"), list):
        return None, "the provider returned no voice list — supply a voice_id directly."

    rows = [_voice_row(v) for v in parsed["voices"] if isinstance(v, dict) and v.get("voice_id")]
    for k, want in filters.items():
        if want:
            want = str(want).lower()
            rows = [r for r in rows if k not in r or str(r[k]).lower() == want]
    if not rows:
        # A filter combination that matches nothing is an ordinary outcome, not an error — say which
        # facets were applied so the caller knows what to relax.
        applied = ", ".join(f"{k}={v}" for k, v in sorted(filters.items()) if v) or "none"
        held = len(parsed["voices"])
        return [], (f"no voice matches all of: {applied}. The account holds {held} voice(s) — drop "
                    "the narrowest facet (use_case is usually the one) and search again before "
                    "concluding there is nothing suitable.")
    return rows[:max(1, int(limit or 8))], None
