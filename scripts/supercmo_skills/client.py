"""supercmo_skills media client — per-capability functions over one route selector.

INTERNAL library functions; the agent never sees them — it sees the *tools* (the MCP server's
tools + the OSS override plugin), which call straight through here. Function names match the tool
names on purpose — one vocabulary: image_generate · video_generate · text_to_speech.

Routing is the LiteLLM-Router pattern: the agent passes a provider-blind model alias; the catalog
maps it to an ordered route list; `_select_route` picks the first available BYO vendor route, else
BYO fal, else the managed proxy. The agent is model-aware, provider-blind.
"""
import base64
import mimetypes
import os
import uuid

import supercmo_env

from . import catalog, paths
from .providers import elevenlabs as _elevenlabs
from .providers import fal as _fal
from .providers import firecrawl as _firecrawl
from .providers import gemini as _gemini
from .providers import openai as _openai
from .providers import xai as _xai

# provider name -> module (uniform contract: BYOK_ENV / is_available / <cap>_generate / <cap>_request_spec).
# Catalog routes only name a provider for capabilities it implements, so a provider is never asked
# for a capability it lacks.
_PROVIDERS = {"fal": _fal, "openai": _openai, "xai": _xai, "elevenlabs": _elevenlabs,
              "gemini": _gemini, "firecrawl": _firecrawl}

# Managed video/tts block server-side on the vendor queue (~minutes); give the proxy HTTP call room.
_MANAGED_LONG_TIMEOUT = 360


def select_route(capability, model, allow_proxy=True):
    """First available BYO vendor route > BYO fal route > managed proxy > none.
    Returns ("direct", provider_module, route) | ("proxy", None, None) | ("none", None, None).

    allow_proxy=False resolves only BYO vendor routes — the SuperCMO proxy reuses this server-side to pick
    a server-keyed vendor and must NOT fall back to the managed proxy (that would make it call itself)."""
    for route in catalog.routes_of(capability, model):
        provider = _PROVIDERS.get(route["provider"])
        if provider and provider.is_available():
            return ("direct", provider, route)
    if allow_proxy and supercmo_env.supercmo_key():
        return ("proxy", None, None)
    return ("none", None, None)


_select_route = select_route   # internal alias (the image/video/tts callers below)


def _setup_hint(capability, model):
    """Name the BYO keys that would serve this model (BYOK-first; managed via SUPERCMO_API_KEY)."""
    keys = []
    for route in catalog.routes_of(capability, model):
        provider = _PROVIDERS.get(route["provider"])
        if provider is not None and provider.BYOK_ENV not in keys:
            keys.append(provider.BYOK_ENV)
    byo = " or ".join(keys) if keys else "a vendor key"
    return (f"Tell the user to set {byo} (their own key from the vendor's dashboard) in the MCP "
            "server config or environment, or a managed SUPERCMO_API_KEY (buy credits + mint at "
            "getsupercmo.ai/settings?tab=keys), or to run the supercmo-setup skill for guided setup, "
            "then retry. Do not substitute a different tool — this key is required to generate.")


# ------------------------------------------------------------------ image ref helpers
def _to_image_ref(path_or_url):
    """URL/data-URI passes through; a local file becomes a base64 data URI."""
    ref = (path_or_url or "").strip()
    if ref.startswith(("http://", "https://", "data:")):
        return ref
    with open(ref, "rb") as f:
        data = f.read()
    mime = mimetypes.guess_type(ref)[0] or "image/png"
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


def _encode_refs(refs):
    """Resolve local paths to data-URIs (URLs pass through). Returns (encoded, None) | (None, error)."""
    try:
        return [_to_image_ref(r) for r in refs], None
    except FileNotFoundError as e:
        return None, {"ok": False, "error": f"reference image not found: {e.filename}"}


def _dispatch(capability, model, inp, kind, provider, route, dry_run, spec_attr, gen_attr, proxy_timeout=120):
    """Shared direct/proxy dispatch for video + tts (image has its own ref-aware body).
    proxy_timeout bounds the managed HTTP call (video/tts block server-side on the vendor queue)."""
    if kind == "direct":
        payload = {"model": model, **inp}
        if dry_run:
            return {"ok": True, "_dry_run": True, "route": route["provider"], "model": model,
                    "request": getattr(provider, spec_attr)(route, payload)}
        return getattr(provider, gen_attr)(route, payload, os.environ.get(provider.BYOK_ENV))
    if kind == "proxy":
        body = {"model": model, "input": inp}
        if dry_run:
            return {"ok": True, "_dry_run": True, "route": "proxy", "model": model,
                    "request": supercmo_env.proxy_spec(capability, body)}
        return supercmo_env.proxy_request(capability, body, timeout=proxy_timeout)
    return {"ok": False, "error": "no_provider_configured", "hint": _setup_hint(capability, model)}


# ------------------------------------------------------------------ local persistence
_MEDIA_EXT = {
    "image/png": ".png", "image/jpeg": ".jpg", "image/jpg": ".jpg", "image/webp": ".webp",
    "video/mp4": ".mp4", "video/webm": ".webm", "video/quicktime": ".mov",
    "audio/mpeg": ".mp3", "audio/mp3": ".mp3", "audio/wav": ".wav", "audio/x-wav": ".wav",
    "audio/ogg": ".ogg", "audio/opus": ".opus", "audio/aac": ".aac",
}
_DEFAULT_EXT = {"image": ".png", "video": ".mp4", "tts": ".mp3"}


def _pick_ext(content_type, url, default):
    if content_type:
        ext = _MEDIA_EXT.get(content_type.split(";")[0].strip().lower())
        if ext:
            return ext
    if url:
        suffix = os.path.splitext(url.split("?")[0])[1].lower()
        if 1 < len(suffix) <= 5:
            return suffix
    return default


def _media_bytes(item):
    """(bytes, content_type) for an item carrying b64, a data: URI, or an http(s) URL; else (None, None)."""
    if item.get("b64"):
        return base64.b64decode(item["b64"]), item.get("content_type")
    url = (item.get("url") or "").strip()
    if url.startswith("data:"):
        try:
            head, payload = url.split(",", 1)
            return base64.b64decode(payload), (head[5:].split(";")[0] or item.get("content_type"))
        except Exception:
            return None, None
    if url.startswith(("http://", "https://")):
        data, ctype, _status, _err = supercmo_env._request_raw("GET", url)
        if data is not None:
            return data, item.get("content_type") or ctype
    return None, None


def _persist_media(result, output_dir, capability):
    """Download/decode generated media to a local dir and add `path` to each item. Best-effort:
    a fetch failure leaves the item's url untouched (persistence never breaks a good generation)."""
    if not isinstance(result, dict) or not result.get("ok"):
        return result
    out_dir = paths.output_dir(output_dir)
    model = str(result.get("model") or capability).replace("/", "-")
    token = uuid.uuid4().hex[:8]
    default_ext = _DEFAULT_EXT.get(capability, ".bin")

    def _save(item, stem):
        try:
            data, ctype = _media_bytes(item)
            if not data:
                return
            os.makedirs(out_dir, exist_ok=True)
            path = os.path.join(out_dir, stem + _pick_ext(ctype, item.get("url"), default_ext))
            with open(path, "wb") as f:
                f.write(data)
            item["path"] = path
            item.pop("b64", None)  # persisted to disk — drop the (huge) inline base64 from the result
        except Exception:
            return  # additive: never raise out of a successful generation

    if isinstance(result.get("images"), list):
        for i, img in enumerate(result["images"]):
            if isinstance(img, dict):
                _save(img, f"{capability}_{model}_{token}_{i}")
    for key in ("video", "audio"):
        item = result.get(key)
        if isinstance(item, dict):
            _save(item, f"{capability}_{model}_{token}")
    result["output_dir"] = out_dir
    return result


# -------------------------------------------------------------------------------- image
def image_generate(prompt, model=None, aspect_ratio=None, resolution=None,
                   reference_images=None, dry_run=False, output_dir=None):
    """One image (text-to-image, or an edit when reference_images are supplied). The tool batches
    these — one call per request object. Returns {ok, model, images} | {ok: False, error, ...}."""
    prompt = (prompt or "").strip()
    if not prompt:
        return {"ok": False, "error": "prompt is required."}
    model = model or catalog.default_model("image")
    if catalog.get("image", model) is None:
        return {"ok": False, "error": f"unknown image model: {model}", "hint": "call list_image_models"}
    aspect = (aspect_ratio or catalog.IMAGE_DEFAULT_ASPECT).lower()
    if aspect not in catalog.IMAGE_ASPECTS:
        return {"ok": False, "error": f"unsupported aspect_ratio: {aspect}", "supported": catalog.IMAGE_ASPECTS}
    res = (resolution or catalog.IMAGE_DEFAULT_RESOLUTION).lower()
    if res not in catalog.IMAGE_RESOLUTIONS:
        return {"ok": False, "error": f"unsupported resolution: {res}", "supported": catalog.IMAGE_RESOLUTIONS}
    refs = reference_images or []
    if not isinstance(refs, list):
        return {"ok": False, "error": "reference_images must be a list of local paths or URLs."}

    kind, provider, route = _select_route("image", model)
    if kind == "none":
        return {"ok": False, "error": "no_provider_configured", "hint": _setup_hint("image", model)}
    if kind == "direct" and len(refs) > route.get("max_refs", 0):
        return {"ok": False,
                "error": f"the {route['provider']} route for {model} accepts at most "
                         f"{route.get('max_refs', 0)} reference image(s); got {len(refs)}.",
                "hint": "drop the reference images, pick a model whose route supports edits, or use the managed key"}
    enc, err = _encode_refs(refs)
    if err:
        return err
    inp = {"prompt": prompt, "aspect_ratio": aspect, "resolution": res, "reference_images": enc}
    out = _dispatch("image", model, inp, kind, provider, route, dry_run,
                    "image_request_spec", "image_generate")
    return out if dry_run else _persist_media(out, output_dir, "image")


# -------------------------------------------------------------------------------- video
def video_generate(prompt, model=None, image_url=None, reference_images=None, duration=None,
                   resolution=None, aspect_ratio=None, generate_audio=None, seed=None, dry_run=False,
                   output_dir=None):
    """Text/image-to-video. Returns {ok, model, video:{url}, duration} | {ok: False, error, ...}. Blocking."""
    prompt = (prompt or "").strip()
    if not prompt:
        return {"ok": False, "error": "prompt is required."}
    model = model or catalog.default_model("video")
    if catalog.get("video", model) is None:
        return {"ok": False, "error": f"unknown video model: {model}", "hint": "call list_video_models"}
    aspect = (aspect_ratio or catalog.DEFAULT_ASPECT).lower()
    if aspect not in catalog.ASPECTS:
        return {"ok": False, "error": f"unsupported aspect_ratio: {aspect}", "supported": catalog.ASPECTS}
    refs = reference_images or []
    if not isinstance(refs, list):
        return {"ok": False, "error": "reference_images must be a list of local paths or URLs."}
    enc_refs, err = _encode_refs(refs)
    if err:
        return err
    enc_image_url = image_url
    if image_url:
        one, err = _encode_refs([image_url])
        if err:
            return err
        enc_image_url = one[0]
    inp = {"prompt": prompt, "image_url": enc_image_url, "reference_images": enc_refs,
           "duration": duration, "resolution": resolution, "aspect_ratio": aspect,
           "generate_audio": generate_audio, "seed": seed}
    kind, provider, route = _select_route("video", model)
    res = _dispatch("video", model, inp, kind, provider, route, dry_run,
                    "video_request_spec", "video_generate", proxy_timeout=_MANAGED_LONG_TIMEOUT)
    return res if dry_run else _persist_media(res, output_dir, "video")


# ---------------------------------------------------------------------------------- tts
def text_to_speech(text, model=None, voice=None, speed=None, dry_run=False, output_dir=None):
    """Text-to-speech. Returns {ok, model, audio:{url|b64}} | {ok: False, error, ...}. Blocking."""
    text = (text or "").strip()
    if not text:
        return {"ok": False, "error": "text is required."}
    model = model or catalog.default_model("tts")
    if catalog.get("tts", model) is None:
        return {"ok": False, "error": f"unknown tts model: {model}", "hint": "call list_voice_models"}
    inp = {"text": text, "voice": voice, "speed": speed}
    kind, provider, route = _select_route("tts", model)
    res = _dispatch("tts", model, inp, kind, provider, route, dry_run,
                    "tts_request_spec", "tts_generate", proxy_timeout=_MANAGED_LONG_TIMEOUT)
    return res if dry_run else _persist_media(res, output_dir, "tts")


# ------------------------------------------------------------------------- extract
def url_extraction(url, prompt=None, schema=None, model=None, dry_run=False):
    """Structured extraction from a web/product URL (fields + image URLs), guided by a prompt or
    JSON schema. Returns {ok, data, metadata} | {ok: False, error, ...}. Returns data, not media."""
    url = (url or "").strip() if isinstance(url, str) else ""
    if not url:
        return {"ok": False, "error": "url is required (an http(s) URL)."}
    if not url.startswith(("http://", "https://")):
        return {"ok": False, "error": "url must be an http(s) URL."}
    model = model or catalog.default_model("extract")
    if catalog.get("extract", model) is None:
        return {"ok": False, "error": f"unknown extract model: {model}"}
    inp = {"url": url, "prompt": (prompt or None), "schema": (schema or None)}
    kind, provider, route = _select_route("extract", model)
    return _dispatch("extract", model, inp, kind, provider, route, dry_run,
                     "extract_request_spec", "extract_generate", proxy_timeout=_MANAGED_LONG_TIMEOUT)


# ------------------------------------------------------------------------ analysis
def image_analysis(image, prompt=None, model=None, dry_run=False):
    """Vision analysis of a local image path or an image URL, answering `prompt`.
    Returns {ok, text} | {ok: False, error, ...}. Returns text, not media."""
    image = (image or "").strip() if isinstance(image, str) else image
    if not image:
        return {"ok": False, "error": "image is required (a local path or an image URL)."}
    model = model or catalog.default_model("analysis")
    if catalog.get("analysis", model) is None:
        return {"ok": False, "error": f"unknown analysis model: {model}"}
    enc, err = _encode_refs([image])
    if err:
        return err
    inp = {"image": enc[0], "prompt": (prompt or None)}
    kind, provider, route = _select_route("analysis", model)
    return _dispatch("analysis", model, inp, kind, provider, route, dry_run,
                     "analyze_request_spec", "analyze_generate")


if __name__ == "__main__":
    _KEYS = ("FAL_KEY", "OPENAI_API_KEY", "XAI_API_KEY", "ELEVENLABS_API_KEY", "GEMINI_API_KEY",
             "FIRECRAWL_API_KEY", "SUPERCMO_API_KEY")

    def _clear():
        for k in _KEYS:
            os.environ.pop(k, None)

    _clear()
    assert image_generate("x", dry_run=True)["error"] == "no_provider_configured"
    assert video_generate("x", dry_run=True)["error"] == "no_provider_configured"
    assert text_to_speech("hi", dry_run=True)["error"] == "no_provider_configured"

    _clear(); os.environ["FAL_KEY"] = "k"
    assert image_generate("x", model="nano-banana", dry_run=True)["route"] == "fal"
    assert video_generate("x", model="veo3.1-fast", dry_run=True)["route"] == "fal"
    assert text_to_speech("hi", model="elevenlabs-v3", dry_run=True)["route"] == "fal"

    os.environ["OPENAI_API_KEY"] = "k"        # openai-direct serves openai-tts
    assert image_generate("x", model="gpt-image-2", dry_run=True)["route"] == "fal"
    assert text_to_speech("hi", model="openai-tts", dry_run=True)["route"] == "openai"

    os.environ["XAI_API_KEY"] = "k"
    assert image_generate("x", model="grok-imagine", dry_run=True)["route"] == "fal"
    assert video_generate("x", model="grok-video", dry_run=True)["route"] == "xai"

    os.environ["ELEVENLABS_API_KEY"] = "k"
    assert text_to_speech("hi", model="elevenlabs-v3", dry_run=True)["route"] == "elevenlabs"
    os.environ["GEMINI_API_KEY"] = "k"
    assert text_to_speech("hi", model="gemini-tts", dry_run=True)["route"] == "gemini"

    _clear(); os.environ["SUPERCMO_API_KEY"] = "k"     # managed fallback when no BYO key
    assert image_generate("x", model="nano-banana", dry_run=True)["route"] == "proxy"
    assert video_generate("x", model="veo3.1-fast", dry_run=True)["route"] == "proxy"
    assert text_to_speech("hi", model="gemini-tts", dry_run=True)["route"] == "proxy"

    # image ref cap: exceeding a fal route's max_refs → actionable error
    _clear(); os.environ["FAL_KEY"] = "k"
    r = image_generate("x", model="nano-banana", reference_images=[f"https://e/{i}.png" for i in range(5)], dry_run=True)
    assert "at most 4" in r.get("error", ""), r

    # extract: BYO firecrawl serves it; missing key → no_provider_configured
    _clear()
    assert url_extraction("https://x/p", dry_run=True)["error"] == "no_provider_configured"
    assert url_extraction("not a url")["error"].startswith("url must be")
    os.environ["FIRECRAWL_API_KEY"] = "k"
    assert url_extraction("https://x/p", prompt="get name", dry_run=True)["route"] == "firecrawl"

    # analysis: BYO gemini serves it (vision via generateContent)
    _clear()
    assert image_analysis("https://x/i.png", dry_run=True)["error"] == "no_provider_configured"
    os.environ["GEMINI_API_KEY"] = "k"
    a = image_analysis("https://x/i.png", prompt="what is it?", dry_run=True)
    assert a["route"] == "gemini" and a["request"]["url"].endswith(":generateContent"), a
    print("client OK")
