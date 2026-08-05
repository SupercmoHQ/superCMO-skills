"""supercmo_skills media client — per-capability functions over one route selector.

INTERNAL library functions; the agent never sees them — it sees the *tools* (the MCP server's
tools + the OSS override plugin), which call straight through here. Function names match the tool
names on purpose — one vocabulary: image_generate · video_generate · audio_generate.

Routing is the LiteLLM-Router pattern: the agent passes a provider-blind model alias; the catalog
maps it to an ordered route list; `_select_route` picks the first available BYO vendor route, else
BYO fal, else the managed proxy. The agent is model-aware, provider-blind.
"""
import base64
import os
import time
import uuid

import supercmo_env

from . import catalog, paths
try:
    from . import telemetry as _telemetry  # anonymous, opt-out usage counts; never required
except Exception:
    _telemetry = None
from .providers import elevenlabs as _elevenlabs
from .providers import fal as _fal
from .providers import firecrawl as _firecrawl
from .providers import gemini as _gemini

# provider name -> module (uniform contract: BYOK_ENV / is_available / <cap>_generate / <cap>_request_spec).
# Catalog routes only name a provider for capabilities it implements, so a provider is never asked
# for a capability it lacks.
_PROVIDERS = {"fal": _fal, "elevenlabs": _elevenlabs,
              "gemini": _gemini, "firecrawl": _firecrawl}


def provider_modules():
    """The name→module provider registry — the single source of which vendors exist and which
    env-var (BYOK_ENV) each reads. Consumed by readiness/doctor/setup_status + the catalog-sync gate."""
    return dict(_PROVIDERS)

# Managed video/audio block server-side on the vendor queue (~minutes); give the proxy HTTP call room.
_MANAGED_LONG_TIMEOUT = 360

# Persisting the finished media to disk is best-effort and runs INSIDE the same blocking tool call
# as the (already-long) generation. Keep its download budget tight so a slow CDN can't push a
# successful generation past the host's per-call timeout — on failure the item keeps its live url.
_MEDIA_DL_TIMEOUT = 30
_MEDIA_DL_RETRIES = 2

# Long-running generations (queued video) are submitted, then polled. A single wait call polls
# for at most _JOB_WAIT_DEADLINE seconds — a wide margin under the MCP host's ~600s per-call
# timeout, leaving room for the final result-fetch + network jitter — then returns a *pending* job
# handle (not an error) that the caller rejoins with job_status(). The job keeps running on the
# vendor regardless, so nothing is ever lost; long jobs just take one more job_status call to finish.
_JOB_WAIT_DEADLINE = 300     # seconds one wait call polls before handing back a pending handle
_POLL_INTERVAL = 3           # first inter-poll sleep
_POLL_INTERVAL_MAX = 15      # backoff ceiling


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


_select_route = select_route   # internal alias (the image/video/audio callers below)


def _setup_hint(capability, model):
    """Two setup paths, managed first, for a no-key generation error. Names the BYO keys that would
    serve this model for the BYOK option."""
    keys = []
    for route in catalog.routes_of(capability, model):
        provider = _PROVIDERS.get(route["provider"])
        if provider is not None and provider.BYOK_ENV not in keys:
            keys.append(provider.BYOK_ENV)
    byo = " or ".join(keys) if keys else "a vendor key"
    return ("No key for this yet. Two options: (A) Managed — run "
            "`npx --yes github:SupercmoHQ/superCMO-skills login` to sign in and pay per use; or "
            f"(B) bring your own {byo} — add it to ~/.supercmo/.env. Then retry. A key is required "
            "to generate. Ask the user which option they want; don't run login unless they choose managed.")


# ------------------------------------------------------------------ image ref helpers
# Media magic bytes → mime. A local ref is accepted ONLY if its actual bytes are a supported media
# file — image, video, or audio (the reference/analysis tools take all three) — so a prompt-injected
# agent can't read a credentials/text file and get it transcribed back through the model
# (CWE-22 / confused-deputy). The mime comes from the bytes, never the spoofable filename.
def _sniff_media_mime(data):
    # images
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image/gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if data[:2] == b"BM" and data[6:10] == b"\x00\x00\x00\x00":   # BMP: reserved dword is 0 in a real file
        return "image/bmp"
    # video (ISO-BMFF mp4/mov, webm/mkv, avi)
    if data[4:8] == b"ftyp":
        return "audio/mp4" if data[8:12] in (b"M4A ", b"M4B ") else "video/mp4"
    if data[:4] == b"\x1aE\xdf\xa3":
        return "video/webm"
    if data[:4] == b"RIFF" and data[8:12] == b"AVI ":
        return "video/x-msvideo"
    # audio (mp3, wav, ogg, flac)
    if data[:3] == b"ID3" or data[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"):
        return "audio/mpeg"
    if data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        return "audio/wav"
    if data[:4] == b"OggS":
        return "audio/ogg"
    if data[:4] == b"fLaC":
        return "audio/flac"
    return None


def _to_image_ref(path_or_url):
    """URL/data-URI passes through; a local file becomes a base64 data URI IF its bytes are actually a
    supported media file (image/video/audio). Accepts a plain path, a `~`-relative path, or a `file://`
    URI. A non-media local file is REJECTED — a credentials/text file must not be read and shipped."""
    ref = (path_or_url or "").strip()
    if ref.startswith(("http://", "https://", "data:")):
        return ref
    if ref.startswith("file://"):                       # agent-supplied file:// URI → local path
        from urllib.parse import unquote, urlparse
        ref = unquote(urlparse(ref).path)
    ref = os.path.expanduser(ref)                        # ~/foo → /Users/…/foo
    with open(ref, "rb") as f:
        data = f.read()
    mime = _sniff_media_mime(data)
    if mime is None:
        raise ValueError(f"reference is not a supported media file (image/video/audio): "
                         f"{os.path.basename(ref)}")
    return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"


def _encode_refs(refs):
    """Resolve local paths to data-URIs (URLs pass through). Returns (encoded, None) | (None, error)."""
    try:
        return [_to_image_ref(r) for r in refs], None
    except ValueError as e:                              # not a supported media file
        return None, {"ok": False, "error": f"reference not usable: {e}"}
    except OSError as e:                                 # missing/unreadable — basename only, no errno/path oracle
        name = os.path.basename(e.filename) if getattr(e, "filename", None) else "reference"
        return None, {"ok": False, "error": f"reference not readable: {name}"}


# capability -> the public tool name, so telemetry speaks one vocabulary across every surface.
_CAP_TOOL = {"image": "image_generate", "video": "video_generate", "tts": "text_to_speech",
             "extract": "url_extraction", "analysis": "image_analysis"}
_ROUTE_LABEL = {"direct": "byok", "proxy": "proxy"}


def _error_code(result, err_cls):
    """A NORMALIZED failure reason from our own fixed vocabulary — NEVER the raw error text
    (vendor messages / interpolated user input can leak through it)."""
    if err_cls:
        return err_cls
    if not isinstance(result, dict) or result.get("ok"):
        return None
    e = str(result.get("error") or "").lower()
    if "no_provider" in e:
        return "no_provider_configured"
    if "unknown" in e and "model" in e:
        return "unknown_model"
    if "insufficient_credits" in e or " 402" in e:
        return "insufficient_credits"
    if "reference image" in e or "accepts at most" in e:
        return "refs_exceeded"
    if "unsupported" in e:
        return "unsupported_param"
    if "required" in e:
        return "missing_param"
    if "rate" in e and "limit" in e:
        return "rate_limited"
    if "timeout" in e or "timed out" in e:
        return "timeout"
    return "provider_error"   # generic bucket — never the raw text


def _record_usage(capability, model, provider_name, kind, t0, result, err_cls):
    """Anonymous usage count from the one dispatch every surface funnels through — carries
    byok-vs-proxy, vendor, model, and a NORMALIZED error code (never raw error text).
    Wrapped so a telemetry fault can never break a generation."""
    if _telemetry is None:
        return
    try:
        ok = bool(isinstance(result, dict) and result.get("ok"))
        _telemetry.record(_CAP_TOOL.get(capability, capability), ok,
                          int((time.monotonic() - t0) * 1000),
                          model_id=model, provider=provider_name,
                          route=_ROUTE_LABEL.get(kind, "none"),
                          error_class=err_cls, error_code=_error_code(result, err_cls))
    except Exception:
        pass


def _dispatch(capability, model, inp, kind, provider, route, dry_run, spec_attr, gen_attr,
              proxy_timeout=120, call_id=None):
    """Shared direct/proxy dispatch for every capability — and the single telemetry choke point.
    proxy_timeout bounds the managed HTTP call (video blocks server-side on the vendor queue)."""
    if kind == "direct" and dry_run:
        payload = {"model": model, **inp}
        return {"ok": True, "_dry_run": True, "route": route["provider"], "model": model,
                "request": getattr(provider, spec_attr)(route, payload)}
    if kind == "proxy" and dry_run:
        body = {"model": model, "input": inp}
        return {"ok": True, "_dry_run": True, "route": "proxy", "model": model,
                "request": supercmo_env.proxy_spec(capability, body)}

    # Real call (dry_run previews are not usage). Telemeter every outcome, all surfaces.
    _prov = route.get("provider") if isinstance(route, dict) else None  # vendor (direct); None on proxy
    _t0 = time.monotonic()
    try:
        if kind == "direct":
            payload = {"model": model, **inp}
            result = getattr(provider, gen_attr)(route, payload, os.environ.get(provider.BYOK_ENV))
        elif kind == "proxy":
            body = {"model": model, "input": inp}
            result = supercmo_env.proxy_request(
                capability, body, call_id=call_id or uuid.uuid4().hex, timeout=proxy_timeout
            )
        else:
            result = {"ok": False, "error": "no_provider_configured", "hint": _setup_hint(capability, model)}
    except Exception as e:
        _record_usage(capability, model, _prov, kind, _t0, None, type(e).__name__)
        raise
    _record_usage(capability, model, _prov, kind, _t0, result, None)
    return result


# ------------------------------------------------------------------ local persistence
_MEDIA_EXT = {
    "image/png": ".png", "image/jpeg": ".jpg", "image/jpg": ".jpg", "image/webp": ".webp",
    "video/mp4": ".mp4", "video/webm": ".webm", "video/quicktime": ".mov",
    "audio/mpeg": ".mp3", "audio/mp3": ".mp3", "audio/wav": ".wav", "audio/x-wav": ".wav",
    "audio/ogg": ".ogg", "audio/opus": ".opus", "audio/aac": ".aac", "audio/pcm": ".pcm",
    "audio/l16": ".pcm", "audio/basic": ".pcm",
}
_DEFAULT_EXT = {"image": ".png", "video": ".mp4", "audio": ".mp3"}


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
        # Tight budget: persistence is best-effort, so a slow/flaky CDN must NOT block the
        # (already-long) generation past the caller's tool-call timeout. On failure we return
        # (None, None) and the item keeps its playable url — the tool still returns promptly.
        t0 = time.time()
        data, ctype, _status, _err = supercmo_env._request_raw(
            "GET", url, timeout=_MEDIA_DL_TIMEOUT, retries=_MEDIA_DL_RETRIES)
        supercmo_env.dbg(f"media download {'ok' if data else 'FAILED'} "
                         f"({len(data) if data else 0}B, {time.time() - t0:.1f}s) {url[:80]}")
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


# ------------------------------------------------------------ long-running jobs (submit / wait / rejoin)
# A job handle is plain JSON returned to the agent and passed back to job_status() to rejoin the SAME
# job. It carries everything a later, stateless call needs: the vendor's own status/response URLs
# (fal — absolute + stateless) or a proxy job_id, plus the capability/model/output_dir needed to
# assemble and persist the final result. No server-side state is kept, so a handle survives a
# tool-call boundary (and even a server restart). The poll loop + finalize live here once; every
# capability (video, future queued audio modes) reuses them — dispatch is on the handle.

def _submit(capability, model, inp, kind, provider, route, call_id=None):
    """Submit a queued job (no wait). Direct → provider.<cap>_submit; proxy → proxy_submit (which may
    answer synchronously). Returns the raw submit/response dict (see _submit_or_run for handling)."""
    if kind == "direct":
        payload = {"model": model, **inp}
        return getattr(provider, f"{capability}_submit")(route, payload, os.environ.get(provider.BYOK_ENV))
    if kind == "proxy":
        return supercmo_env.proxy_submit(capability, {"model": model, "input": inp},
                                         call_id=call_id or uuid.uuid4().hex,
                                         timeout=_MANAGED_LONG_TIMEOUT)
    return {"ok": False, "error": "no_provider_configured", "hint": _setup_hint(capability, model)}


def _make_handle(capability, model, kind, sub, output_dir, adjusted=None):
    """Build the stateless pending handle from a successful submit."""
    h = {"status": "pending", "capability": capability, "model": model, "output_dir": output_dir}
    if kind == "proxy":
        h["provider"], h["job_id"] = "proxy", sub.get("job_id")
    else:                                    # queued direct vendor (fal)
        h["provider"] = "fal"
        h["request_id"] = sub.get("request_id")
        h["status_url"], h["response_url"] = sub.get("status_url"), sub.get("response_url")
    if adjusted:
        h["duration_adjusted"] = adjusted
    return h


def _poll_once(handle):
    """One status check for a handle. Pending → {ok: True, done: False, ...}; completed →
    {ok: True, done: True, <video|audio>, ...}; else {ok: False, ...}. Reads the key from env each
    call (stateless)."""
    cap = handle.get("capability")
    if handle.get("provider") == "proxy":
        return supercmo_env.proxy_job_status(handle.get("job_id"))
    key = os.environ.get(_fal.BYOK_ENV)
    if not key:
        return {"ok": False, "error": "no_provider_configured",
                "hint": f"set {_fal.BYOK_ENV} (the key that submitted this job) and retry."}
    return getattr(_fal, f"{cap}_status")(handle.get("status_url"), handle.get("response_url"), key)


def _finalize(handle, status):
    """Assemble + persist the final media envelope from a completed poll (adds model + any
    duration_adjusted carried on the handle)."""
    cap = handle.get("capability")
    res = {"ok": True, "model": handle.get("model")}
    if cap == "video":
        res["video"] = status.get("video")
        res["duration"] = status.get("duration")
    elif cap == "audio":
        res["audio"] = status.get("audio")
    elif cap == "image":
        res["images"] = status.get("images")
        if status.get("seed") is not None:
            res["seed"] = status.get("seed")
    if handle.get("duration_adjusted"):
        res["duration_adjusted"] = handle["duration_adjusted"]
    return _persist_media(res, handle.get("output_dir"), cap)


def _wait_for_job(handle, deadline_s=None):
    """Poll a handle to completion, but for at most deadline_s (default _JOB_WAIT_DEADLINE). On
    completion → the finalized media; on a terminal error → that error; on budget exhaustion → the
    unchanged pending handle (rejoin later with job_status)."""
    deadline = _JOB_WAIT_DEADLINE if deadline_s is None else deadline_s
    t0, interval = time.time(), _POLL_INTERVAL
    while True:
        st = _poll_once(handle)
        if st.get("ok") and st.get("done"):
            return _finalize(handle, st)
        if not st.get("ok") and not st.get("transient"):
            return st                                  # real failure (vendor error / bad handle) — stop
        # still running, or a transient poll hiccup (timeout/network): keep waiting, don't give up the
        # job — a slow poll must never turn a live job into a failure the caller would resubmit.
        if time.time() - t0 >= deadline:
            return handle                              # hand back the pending handle → rejoin via job_status
        time.sleep(interval)
        interval = min(interval * 1.5, _POLL_INTERVAL_MAX)


def _submit_or_run(capability, model, inp, kind, provider, route, output_dir, wait, deadline_s,
                   adjusted=None, call_id=None):
    """Submit a generation and either wait to completion or hand back a pending handle. Synchronous
    providers (direct non-queued, e.g. elevenlabs speech) and a synchronous proxy return
    the finished media directly — only queued jobs produce a handle."""
    if kind == "none":
        return {"ok": False, "error": "no_provider_configured", "hint": _setup_hint(capability, model)}
    if kind == "direct" and not hasattr(provider, f"{capability}_submit"):   # synchronous vendor
        payload = {"model": model, **inp}
        res = getattr(provider, f"{capability}_generate")(route, payload, os.environ.get(provider.BYOK_ENV))
        if adjusted and isinstance(res, dict):
            res["duration_adjusted"] = adjusted
        return _persist_media(res, output_dir, capability)
    sub = _submit(capability, model, inp, kind, provider, route, call_id=call_id)
    if not sub.get("ok"):
        return sub
    if kind == "proxy" and not sub.get("job_id"):     # proxy answered synchronously
        if adjusted:
            sub["duration_adjusted"] = adjusted
        return _persist_media(sub, output_dir, capability)
    handle = _make_handle(capability, model, kind, sub, output_dir, adjusted)
    return handle if not wait else _wait_for_job(handle, deadline_s)


def job_status(job, wait=True, deadline_s=None):
    """Rejoin a previously submitted generation by its handle and retrieve the finished media. Pass
    the exact `job` object a prior video_generate/audio_generate (or job_status) returned with
    status "pending" — never re-submit. With wait=True (default) it polls up to deadline_s and
    returns either the finished media or, if the job is still running, the same pending handle to
    call again; wait=False does a single check. Returns {ok, video|audio, ...} | pending handle |
    {ok: False, error, ...}."""
    if not isinstance(job, dict) or job.get("provider") not in ("fal", "proxy") \
            or not job.get("capability"):
        return {"ok": False, "error": "invalid job handle",
                "hint": "pass the exact pending job object a prior generate/job_status call returned."}
    if wait:
        return _wait_for_job(job, deadline_s)
    st = _poll_once(job)
    if not st.get("ok"):
        return st
    return _finalize(job, st) if st.get("done") else job


def is_pending(result):
    """True if a per-item result is a still-running job handle (submitted, not yet finished)."""
    return isinstance(result, dict) and result.get("status") == "pending"


def job_ok(result):
    """Whether a per-item generation result is healthy: it either finished (`ok`) or is still
    running (a `pending` handle). Batch tools use this for their top-level `ok` so a batch isn't
    reported as failed just because some items are still generating."""
    return bool(result.get("ok")) or is_pending(result)


# -------------------------------------------------------------------------------- image
def image_generate(prompt, model=None, aspect_ratio=None, resolution=None,
                   reference_images=None, dry_run=False, output_dir=None, wait=True, deadline_s=None,
                   call_id=None):
    """One image (text-to-image, or an edit when reference_images are supplied). The tool batches
    these — one call per request object. Images are submitted on the queue and polled: a fast image
    returns {ok, model, images} on the first poll, a slow one (heavy model / 4k / large batch) comes
    back as a pending job handle ({status: "pending", ...}) to rejoin with job_status(). wait=False
    returns the handle immediately. Returns {ok: False, error, ...} on a validation/submit error."""
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
    if dry_run:
        return _dispatch("image", model, inp, kind, provider, route, dry_run,
                         "image_request_spec", "image_generate")
    return _submit_or_run(
        "image", model, inp, kind, provider, route, output_dir, wait, deadline_s,
        call_id=call_id,
    )


# -------------------------------------------------------------------------------- video
_VIDEO_REF_FIELDS = ("reference_images", "reference_videos", "reference_audios")


def _nearest(value, allowed):
    """Nearest allowed number to `value` (ties break to the smaller)."""
    return min(allowed, key=lambda a: (abs(a - value), a))


# The tool-level media fields that choose a video endpoint (frame pins + reference kinds).
_VIDEO_MEDIA_FIELDS = ("start_frame_image", "end_frame_image") + _VIDEO_REF_FIELDS


def _resolve_video(base_route, populated):
    """The video endpoint chosen by the supplied media, plus the route carrying that endpoint's
    id/media/limits. Shared by the BYOK `video_generate` and the managed path (`generate_managed`)
    so endpoint resolution has ONE codepath and can't drift. Returns (ep, resolved), or (None, None)
    when no single endpoint accepts `populated`."""
    ep = catalog.video_endpoint_for(base_route, populated)
    if ep is None:
        return None, None
    resolved = {**base_route, "id": ep["id"], "media": ep["media"], "aspects": ep["aspects"],
                "durations": ep["durations"], "resolutions": ep["resolutions"]}
    return ep, resolved


def video_generate(prompt, model=None, aspect_ratio=None, duration=None, resolution=None,
                   start_frame_image=None, end_frame_image=None, reference_images=None,
                   reference_videos=None, reference_audios=None, generate_audio=None,
                   dry_run=False, output_dir=None, wait=True, deadline_s=None, call_id=None):
    """Text / image / reference-to-video. Video generation is queued and long-running: the clip is
    submitted, then polled. With wait=True (default) this returns the finished {ok, model, video:{url},
    duration, ...} when it completes within one wait window, or a pending job handle ({status:
    "pending", ...}) if it runs longer — rejoin that with job_status(); with wait=False it returns the
    handle immediately. Returns {ok: False, ...} on a validation/submit error.
    Routes to the model's text-to-video / image-to-video / first-last-frame / reference-to-video
    endpoint by which media are supplied (frame-pins and references can't combine — different endpoints).
    Validates aspect/resolution against the chosen endpoint (error) and snaps an out-of-range duration to
    the nearest supported value (reported in `duration_adjusted`)."""
    prompt = (prompt or "").strip()
    if not prompt:
        return {"ok": False, "error": "prompt is required."}
    model = model or catalog.default_model("video")
    if catalog.get("video", model) is None:
        return {"ok": False, "error": f"unknown video model: {model}", "hint": "call list_video_models"}
    route = catalog.routes_of("video", model)[0]

    refs = {"reference_images": reference_images, "reference_videos": reference_videos,
            "reference_audios": reference_audios}
    for k, v in refs.items():
        if v is not None and not isinstance(v, list):
            return {"ok": False, "error": f"{k} must be a list of local paths or URLs."}
        refs[k] = v or []
    frames = {"start_frame_image": start_frame_image, "end_frame_image": end_frame_image}
    if end_frame_image and not start_frame_image:
        return {"ok": False, "error": "end_frame_image needs a start_frame_image too."}

    populated = {k for k, v in frames.items() if v} | {k for k, v in refs.items() if v}
    ep, resolved = _resolve_video(route, populated)
    if ep is None:
        return {"ok": False,
                "error": f"{model} can't take that combination of inputs in one call — start/end frames "
                         "and references use different generation modes, and not every model accepts every "
                         "reference kind.",
                "accepts_media": sorted(catalog.video_media_kinds(route)) or "none (text-to-video only)",
                "hint": "supply either frame(s) or references (not both), using only kinds this model accepts"}
    missing = [k for k in ep.get("requires", ()) if k not in populated]
    if missing:                                    # e.g. Kling references only work alongside a start frame
        names = ", ".join(m.replace("_", " ") for m in missing)
        return {"ok": False, "error": f"{model} requires a {names} for this mode — its references only "
                f"work together with a start frame (there is no reference-only mode).",
                "hint": "pass start_frame_image (the reference/subject image) as well"}

    for k in _VIDEO_REF_FIELDS:
        cap = route["max_refs"].get(k)
        if refs[k] and cap is not None and len(refs[k]) > cap:
            return {"ok": False, "error": f"{model} accepts at most {cap} {k.replace('_', ' ')}; got {len(refs[k])}."}
    combined_max = route.get("combined_ref_max")   # shared budget across image + video references
    combined = len(refs["reference_images"]) + len(refs["reference_videos"])
    if combined_max is not None and combined > combined_max:
        return {"ok": False, "error": f"{model} accepts at most {combined_max} references (images + "
                f"videos combined); got {combined}."}

    if aspect_ratio and ep["aspects"] and aspect_ratio.lower() not in ep["aspects"]:
        return {"ok": False, "error": f"{model} does not support aspect_ratio '{aspect_ratio}' in this mode",
                "supported": ep["aspects"]}
    if resolution and ep["resolutions"] and resolution.lower() not in ep["resolutions"]:
        return {"ok": False, "error": f"{model} does not support resolution '{resolution}' in this mode",
                "supported": ep["resolutions"]}
    dur, adjusted = duration, None
    if duration is not None and ep["durations"] and int(duration) not in ep["durations"]:
        dur = _nearest(int(duration), ep["durations"])       # snap-and-report (never a dead-end)
        adjusted = {"requested": int(duration), "used": dur}

    enc = {}                                                 # encode media (local files → data-URIs)
    for k, v in frames.items():
        if v:
            one, err = _encode_refs([v])
            if err:
                return err
            enc[k] = one[0]
    for k in _VIDEO_REF_FIELDS:
        if refs[k]:
            lst, err = _encode_refs(refs[k])
            if err:
                return err
            enc[k] = lst

    inp = {**enc, "prompt": prompt, "duration": dur, "resolution": resolution,
           "aspect_ratio": (aspect_ratio.lower() if aspect_ratio else None), "generate_audio": generate_audio}
    kind, provider, _sel = _select_route("video", model)
    if dry_run:
        res = _dispatch("video", model, inp, kind, provider, resolved, dry_run,
                        "video_request_spec", "video_generate")
        if adjusted and isinstance(res, dict):
            res["duration_adjusted"] = adjusted
        return res
    return _submit_or_run("video", model, inp, kind, provider, resolved, output_dir,
                          wait, deadline_s, adjusted, call_id=call_id)


# -------------------------------------------------------------------------------- audio
def list_voices(search=None, gender=None, accent=None, age=None, use_case=None, language=None,
                limit=8):
    """(payload) for the list_voices tool — the voices saved in the active account, each with labels
    and a preview_url. Routes to whichever provider serves audio, so the managed lane returns our
    account's voices and a BYO key returns the caller's own."""
    kind, provider, _route = _select_route("audio", catalog.default_model("audio"))
    if kind == "proxy":
        # Managed lane: our own account's voices, resolved server-side via /proxy/voices.
        return supercmo_env.proxy_request("voices", {
            "search": search, "gender": gender, "accent": accent, "age": age,
            "use_case": use_case, "language": language, "limit": limit},
            call_id=f"voices-{uuid.uuid4().hex}")
    if kind != "direct" or not hasattr(provider, "list_voices"):
        return {"ok": False, "error": "no_provider_configured",
                "hint": _setup_hint("audio", catalog.default_model("audio"))}
    voices, problem = provider.list_voices(
        os.environ.get(provider.BYOK_ENV), search=search, limit=limit,
        gender=gender, accent=accent, age=age, use_case=use_case, language=language)
    if voices is None:                       # the list could not be read at all
        return {"ok": False, "error": "no_voices_available", "hint": problem}
    if not voices:                           # searched fine, nothing matched — not a failure
        return {"ok": True, "count": 0, "voices": [], "hint": problem}
    return {"ok": True, "count": len(voices), "voices": voices,
            "hint": "pass a row's `voice_id` as `voice` on audio_generate; play `preview_url` to "
                    "audition it before choosing."}


def audio_generate(text=None, type="speech", model=None, voice=None, speed=None, stability=None,
                   similarity_boost=None, style=None, format=None, dry_run=False, output_dir=None,
                   wait=True, deadline_s=None, call_id=None):
    """Generate one standalone audio clip. Returns {ok, model, audio:{url|b64, path}} | {ok: False,
    error, ...}. `type` selects the mode; an unsupported value errors with the supported set."""
    if type not in catalog.AUDIO_TYPES:
        return {"ok": False, "error": f"unknown audio type: {type}",
                "supported": list(catalog.AUDIO_TYPES)}
    text = (text or "").strip()
    if not text:
        return {"ok": False, "error": "text is required — the exact words to speak."}
    # No fallback voice: the vendor needs an id in the URL, and substituting an arbitrary one would
    # silently read brand copy in a stranger's voice. Make the caller choose.
    if not (voice or "").strip():
        return {"ok": False, "error": "voice is required.",
                "hint": "call list_voices with the brief's requirements and pass a row's `voice_id`."}
    model = model or catalog.default_model("audio")
    entry = catalog.get("audio", model)
    if entry is None:
        return {"ok": False, "error": f"unknown audio model: {model}", "hint": "call list_audio_models"}
    if type not in entry.get("types", []):
        return {"ok": False, "error": f"model {model} does not support audio type: {type}",
                "supported": list(entry.get("types", []))}
    if format is not None and format not in catalog.AUDIO_FORMATS:
        return {"ok": False, "error": f"unsupported format: {format}",
                "supported": list(catalog.AUDIO_FORMATS)}
    # The vendor publishes a range only for speed (0.7-1.2). The 0-1 bound on the other three is
    # ours: their defaults are 0.5/0.75/0 and nothing documents a ceiling, so this is a guard against
    # a nonsense value reaching the API, not a documented limit. Snap rather than reject, and say so.
    adjusted = {}
    unit = {"stability": stability, "style": style, "similarity_boost": similarity_boost,
            "speed": speed}
    for k, v in unit.items():
        if v is None:
            continue
        try:
            v = float(v)
        except (TypeError, ValueError):
            return {"ok": False, "error": f"{k} must be a number; got {v!r}."}
        lo, hi = (0.7, 1.2) if k == "speed" else (0.0, 1.0)
        unit[k] = min(hi, max(lo, v))
        if unit[k] != v:
            adjusted[k] = {"requested": v, "used": unit[k]}
    inp = {"text": text, "voice": voice, "format": format, **unit}
    kind, provider, route = _select_route("audio", model)
    # A vendor may reject an input shape only it can judge (an unresolvable voice, say). Check it
    # here so a dry run reports the same error a real call would, instead of previewing a bad request.
    validate = getattr(provider, "audio_validate", None) if kind == "direct" else None
    err = validate({"model": model, **inp}) if validate else None
    if err:
        return err
    if dry_run:
        res = _dispatch("audio", model, inp, kind, provider, route, dry_run,
                        "audio_request_spec", "audio_generate")
    else:
        res = _submit_or_run(
            "audio", model, inp, kind, provider, route, output_dir, wait, deadline_s,
            call_id=call_id,
        )
    if adjusted and isinstance(res, dict) and res.get("ok"):
        res["adjusted"] = adjusted
    return res


# ------------------------------------------------------------------------- extract
def url_extraction(url, prompt=None, schema=None, model=None, dry_run=False, call_id=None):
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
                     "extract_request_spec", "extract_generate", proxy_timeout=_MANAGED_LONG_TIMEOUT,
                     call_id=call_id)


# ------------------------------------------------------------------------ analysis
def image_analysis(image, prompt=None, model=None, dry_run=False, call_id=None):
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
                     "analyze_request_spec", "analyze_generate", call_id=call_id)


def video_analysis(video, prompt=None, model=None, dry_run=False, call_id=None):
    """Vision analysis of a local video path or a video URL, answering `prompt`.
    Returns {ok, text} | {ok: False, error, ...}. Returns text, not media. Analyzes a clip inline —
    a very large file may exceed the request limit."""
    video = (video or "").strip() if isinstance(video, str) else video
    if not video:
        return {"ok": False, "error": "video is required (a local path or a video URL)."}
    model = model or catalog.default_model("analysis")
    if catalog.get("analysis", model) is None:
        return {"ok": False, "error": f"unknown analysis model: {model}"}
    enc, err = _encode_refs([video])
    if err:
        return err
    inp = {"video": enc[0], "prompt": (prompt or None)}
    kind, provider, route = _select_route("analysis", model)
    return _dispatch("analysis", model, inp, kind, provider, route, dry_run,
                     "analyze_video_request_spec", "analyze_video_generate", call_id=call_id)


# ------------------------------------------------- managed (server-side) generation for the proxy
def can_serve_managed(capability, model):
    """True when a server vendor key is set for a direct route of (capability, model). The managed
    proxy checks this BEFORE charging — a missing server key is our misconfiguration (a 503), never
    a user debit followed by a refund."""
    return select_route(capability, model, allow_proxy=False)[0] == "direct"


# Every agent-supplied media reference the managed proxy might inline or forward. Server-side these
# must be http(s) URLs or data: URIs only — see _unsafe_managed_ref.
_MANAGED_MEDIA_REF_FIELDS = (
    "reference_images", "reference_videos", "reference_audios",
    "start_frame_image", "end_frame_image", "image_url", "image", "video", "audio",
)


def _unsafe_managed_ref(inp):
    """The first media-ref field in `inp` that is NOT an http(s) URL or a data: URI, else None. Server-
    side, an agent-supplied bare/relative path or file:// URI would target the SERVER's filesystem (LFI),
    never the caller's box, so the managed proxy refuses them (BYOK, on the caller's own machine, still
    accepts local paths — they're encoded to data URIs before they ever reach here). An allowed http(s)
    ref is still fetched behind the SSRF guard downstream (safe_fetch_bytes)."""
    for field in _MANAGED_MEDIA_REF_FIELDS:
        v = inp.get(field)
        for r in (v if isinstance(v, list) else [v]):
            if isinstance(r, str) and r.strip() and not r.strip().lower().startswith(
                    ("http://", "https://", "data:")):
                return field
    return None


def generate_managed(capability, model, inp):
    """The ONE server-side entry the managed proxy calls. Resolves the route exactly as the BYOK
    client does — including the video endpoint — then runs the provider with the SERVER key (read
    from the resolved provider's BYOK_ENV in the process environment, the same key select_route
    required). Returns the provider's raw result dict, or {ok: False, error, hint} on a resolution
    failure. No telemetry, no persistence, no dry-run: the proxy owns billing + delivery. `inp` is
    the semantic input the client posts to the proxy ({prompt, ...}; media refs already data-URI-encoded).

    Provider method names are NOT uniformly `<cap>_generate`: analysis dispatches to
    `analyze_generate` / `analyze_video_generate` by whether an image or a video was supplied."""
    kind, provider, route = select_route(capability, model, allow_proxy=False)
    if kind != "direct" or provider is None:
        return {"ok": False, "error": "no_provider_configured",
                "hint": f"no server vendor key for any {capability} route of '{model}'"}
    bad = _unsafe_managed_ref(inp)
    if bad is not None:
        return {"ok": False, "error": "unsafe_reference",
                "hint": f"managed generation accepts only http(s) URLs or data: URIs for `{bad}` — a "
                        "local path or file:// is not allowed server-side."}
    key = os.environ.get(provider.BYOK_ENV)
    if capability == "video":
        populated = {f for f in _VIDEO_MEDIA_FIELDS if inp.get(f)}
        ep, route = _resolve_video(route, populated)
        if ep is None:
            return {"ok": False, "error": "unsupported_media_combination",
                    "hint": f"{model} can't take that combination of inputs in one call"}
        gen_attr = "video_generate"
    elif capability == "analysis":
        gen_attr = "analyze_video_generate" if inp.get("video") else "analyze_generate"
    else:
        gen_attr = f"{capability}_generate"          # image_generate / audio_generate / extract_generate
    return getattr(provider, gen_attr)(route, {"model": model, **inp}, key)


def list_voices_managed(filters):
    """Server-side voice discovery for the managed proxy: our own audio account's voices, read with
    the server key. `filters` = {search, gender, accent, age, use_case, language, limit}. Returns the
    SAME payload shape the BYO `list_voices` returns, so a managed user has full voice discovery."""
    kind, provider, _route = select_route("audio", catalog.default_model("audio"), allow_proxy=False)
    if kind != "direct" or not hasattr(provider, "list_voices"):
        return {"ok": False, "error": "no_voices_available",
                "hint": "the managed audio provider is not configured server-side."}
    f = filters or {}
    voices, problem = provider.list_voices(
        os.environ.get(provider.BYOK_ENV), search=f.get("search"), limit=int(f.get("limit") or 8),
        gender=f.get("gender"), accent=f.get("accent"), age=f.get("age"),
        use_case=f.get("use_case"), language=f.get("language"))
    if voices is None:
        return {"ok": False, "error": "no_voices_available", "hint": problem}
    if not voices:
        return {"ok": True, "count": 0, "voices": [], "hint": problem}
    return {"ok": True, "count": len(voices), "voices": voices,
            "hint": "pass a row's `voice_id` as `voice` on audio_generate; play `preview_url` to audition it."}


if __name__ == "__main__":
    _KEYS = ("FAL_KEY", "ELEVENLABS_API_KEY", "GEMINI_API_KEY",
             "FIRECRAWL_API_KEY", "SUPERCMO_API_KEY")

    # Route tests below build their own credential states in os.environ. Keep the user's
    # ~/.supercmo/.env from repopulating those keys between _clear() and a route lookup.
    _REAL_RELOAD_KEYS = supercmo_env.reload_keys
    supercmo_env.reload_keys = lambda: None

    def _clear():
        for k in _KEYS:
            os.environ.pop(k, None)

    _clear()
    assert image_generate("x", dry_run=True)["error"] == "no_provider_configured"
    assert video_generate("x", dry_run=True)["error"] == "no_provider_configured"
    assert audio_generate("hi", voice="V"*20, dry_run=True)["error"] == "no_provider_configured"

    _clear(); os.environ["FAL_KEY"] = "k"      # fal serves image / video (incl. grok via fal)
    assert image_generate("x", model="nano-banana", dry_run=True)["route"] == "fal"
    assert image_generate("x", model="grok-imagine", dry_run=True)["route"] == "fal"
    assert video_generate("x", model="seedance-2.0", dry_run=True)["route"] == "fal"
    assert video_generate("x", model="grok-imagine-video", dry_run=True)["route"] == "fal"
    assert image_generate("x", model="gpt-image-2", dry_run=True)["route"] == "fal"
    # no fal route for audio — a fal-only user is told which key to set
    assert audio_generate("hi", voice="V"*20, dry_run=True)["error"] == "no_provider_configured"
    assert "ELEVENLABS_API_KEY" in audio_generate("hi", voice="V"*20, dry_run=True)["hint"]

    os.environ["ELEVENLABS_API_KEY"] = "k"
    _V = "EXAVITQu4vr4xnSDxMaL"                # an id-shaped voice, as list_voices returns
    for _m in ("eleven-v3", "eleven-multilingual-v2", "eleven-flash-v2.5"):
        assert audio_generate("hi", voice=_V, model=_m, dry_run=True)["route"] == "elevenlabs", _m
    _spec = audio_generate("hi", voice=_V, stability=0.4, speed=1.1, format="wav",
                           dry_run=True)["request"]
    assert _spec["url"].endswith("output_format=wav_44100") and _V in _spec["url"], _spec
    assert _spec["body"]["model_id"] == "eleven_v3", _spec           # default alias -> vendor id
    assert _spec["body"]["voice_settings"] == {"stability": 0.4, "speed": 1.1}, _spec
    assert _spec["headers"]["xi-api-key"] == "***", _spec            # key never leaks into a dry run
    # there is NO default voice — omitting it is an error, not a silent stock read
    _nv = audio_generate("hi", dry_run=True)
    assert _nv["error"] == "voice is required." and "list_voices" in _nv["hint"], _nv
    # a display name is rejected before the request goes out, on both dry run and real call
    assert audio_generate("hi", voice="Rachel", dry_run=True)["error"] == "not a voice id: Rachel"
    # unknown alias / unsupported mode / bad format each fail with the supported set
    assert audio_generate("hi", voice=_V, model="nope", dry_run=True)["error"].startswith("unknown audio model")
    _t = audio_generate("hi", voice=_V, type="music", dry_run=True)
    assert _t["error"] == "unknown audio type: music" and _t["supported"] == ["speech"], _t
    assert audio_generate("hi", voice=_V, format="flac", dry_run=True)["supported"] == catalog.AUDIO_FORMATS
    assert audio_generate("   ", voice=_V, dry_run=True)["error"].startswith("text is required")
    # out-of-range 0-1 knobs snap and are reported rather than reaching the vendor
    _a = audio_generate("hi", voice=_V, stability=5, style=-2, speed=9, dry_run=True)
    assert _a["adjusted"]["stability"] == {"requested": 5.0, "used": 1.0}, _a
    assert _a["adjusted"]["speed"] == {"requested": 9.0, "used": 1.2}, _a   # speed has its own band
    assert _a["request"]["body"]["voice_settings"] == {"stability": 1.0, "style": 0.0, "speed": 1.2}, _a
    # a non-numeric knob is an error, not an unhandled TypeError out of the library
    assert audio_generate("hi", voice=_V, stability="Creative", dry_run=True)["error"] == (
        "stability must be a number; got 'Creative'.")

    _clear(); os.environ["SUPERCMO_API_KEY"] = "k"     # managed fallback when no BYO key
    assert image_generate("x", model="nano-banana", dry_run=True)["route"] == "proxy"
    assert video_generate("x", model="seedance-2.0", dry_run=True)["route"] == "proxy"
    assert audio_generate("hi", voice="V"*20, dry_run=True)["route"] == "proxy"
    # the managed lane now browses OUR account's voices via /proxy/voices (stub the network)
    _real_pr = supercmo_env.proxy_request
    supercmo_env.proxy_request = lambda cap, body, **kw: {"ok": True, "_cap": cap, "voices": [{"voice_id": "srv"}]}
    try:
        _mv = list_voices(search="warm")
        assert _mv["ok"] and _mv["_cap"] == "voices" and _mv["voices"][0]["voice_id"] == "srv", _mv
    finally:
        supercmo_env.proxy_request = _real_pr
    # list_voices_managed: server-side discovery with the server key (stub the provider)
    _clear(); os.environ["ELEVENLABS_API_KEY"] = "srvkey"
    _real_lv = _elevenlabs.list_voices
    _elevenlabs.list_voices = lambda key, **kw: ([{"voice_id": "acct1"}], None) if key == "srvkey" else (None, "bad key")
    try:
        _r = list_voices_managed({"search": "warm", "limit": 3})
        assert _r["ok"] and _r["voices"][0]["voice_id"] == "acct1", _r
    finally:
        _elevenlabs.list_voices = _real_lv
    _clear(); os.environ["SUPERCMO_API_KEY"] = "k"

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

    # ---- long-running jobs: submit → pending handle → rejoin (stub the network) ----
    _clear(); os.environ["FAL_KEY"] = "k"
    _real = supercmo_env._request
    _script = []

    def _stub(method, url, body=None, headers=None, timeout=120, retries=None):
        return _script.pop(0)
    supercmo_env._request = _stub
    try:
        # wait=False → a well-formed pending handle, no polling
        _script[:] = [({"request_id": "r1", "status_url": "https://q/s", "response_url": "https://q/r"}, 200, None)]
        h = video_generate("a cat walking", model="seedance-2.0", wait=False)
        assert h["status"] == "pending" and h["provider"] == "fal" and h["capability"] == "video", h
        assert h["status_url"] == "https://q/s" and h["response_url"] == "https://q/r" and h["model"] == "seedance-2.0", h

        # job_status(wait=False) while still running → the same pending handle back
        _script[:] = [({"status": "IN_PROGRESS"}, 200, None)]
        again = job_status(h, wait=False)
        assert again is h, again

        # job_status(wait=False) once completed → finalized video (persist is best-effort; url present)
        _script[:] = [({"status": "COMPLETED"}, 200, None),
                      ({"video": {"url": "https://cdn/v.mp4", "duration": 6}}, 200, None)]
        done = job_status(h, wait=False)
        assert done["ok"] and done["model"] == "seedance-2.0" and done["video"]["url"] == "https://cdn/v.mp4", done

        # a garbage handle is rejected, not polled
        bad = job_status({"nope": 1}, wait=False)
        assert not bad["ok"] and bad["error"] == "invalid job handle", bad

        # image is queued too: wait=False → image handle; rejoin once completed → images list
        _script[:] = [({"request_id": "i1", "status_url": "https://q/is", "response_url": "https://q/ir"}, 200, None)]
        ih = image_generate("a red logo", model="nano-banana", wait=False)
        assert ih["status"] == "pending" and ih["capability"] == "image" and ih["provider"] == "fal", ih
        _script[:] = [({"status": "COMPLETED"}, 200, None),
                      ({"images": [{"url": "https://cdn/i.png"}], "seed": 7}, 200, None)]
        idone = job_status(ih, wait=False)
        assert idone["ok"] and idone["images"][0]["url"] == "https://cdn/i.png" and idone["seed"] == 7, idone
    finally:
        supercmo_env._request = _real

    # wait=True with no provider configured still errors cleanly (no network)
    _clear()
    assert video_generate("x", model="seedance-2.0")["error"] == "no_provider_configured"

    # ---- generate_managed: the ONE server-side entry the proxy calls (stub providers, no network) ----
    _seen = {}
    def _capture(name):
        def _fn(route, payload, key):
            _seen[name] = {"route": route, "payload": payload, "key": key}
            return {"ok": True, "model": payload.get("model"), name: {"url": "x"}}
        return _fn

    _clear(); os.environ["FAL_KEY"] = "sk"
    _save = {(_fal, a): getattr(_fal, a) for a in ("image_generate", "video_generate")}
    for (m, a) in _save:
        setattr(m, a, _capture(a))
    r = generate_managed("image", "nano-banana", {"prompt": "x", "reference_images": []})
    assert r["ok"] and _seen["image_generate"]["route"]["provider"] == "fal" and _seen["image_generate"]["key"] == "sk", r
    # video: the resolved route must carry a concrete endpoint id (the base route has none)
    generate_managed("video", "seedance-2.0", {"prompt": "x"})
    assert _seen["video_generate"]["route"]["id"].endswith("text-to-video"), _seen["video_generate"]["route"]
    generate_managed("video", "seedance-2.0", {"prompt": "x", "start_frame_image": "data:,x"})
    assert _seen["video_generate"]["route"]["id"].endswith("image-to-video"), _seen["video_generate"]["route"]
    for (m, a), f in _save.items():
        setattr(m, a, f)
    # analysis dispatches to analyze_generate vs analyze_video_generate by the input key
    _clear(); os.environ["GEMINI_API_KEY"] = "sk"; _seen.clear()
    _saveg = {a: getattr(_gemini, a) for a in ("analyze_generate", "analyze_video_generate")}
    for a in _saveg:
        setattr(_gemini, a, _capture(a))
    generate_managed("analysis", "gemini-flash-latest", {"image": "data:,x", "prompt": None})
    assert "analyze_generate" in _seen and "analyze_video_generate" not in _seen, _seen
    _seen.clear()
    generate_managed("analysis", "gemini-flash-latest", {"video": "data:,x", "prompt": None})
    assert "analyze_video_generate" in _seen, _seen
    for a, f in _saveg.items():
        setattr(_gemini, a, f)
    # no server key -> clean no_provider_configured (never raises)
    _clear()
    assert generate_managed("image", "nano-banana", {"prompt": "x"})["error"] == "no_provider_configured"
    # can_serve_managed: server-key readiness (the proxy checks this BEFORE charging)
    assert can_serve_managed("image", "nano-banana") is False
    os.environ["FAL_KEY"] = "sk"
    assert can_serve_managed("image", "nano-banana") is True
    assert can_serve_managed("audio", "eleven-v3") is False       # no elevenlabs key set
    _clear()

    # ---- server-side reference safety (Step 8): the managed entry must refuse a local/file:// ref
    # (it would read the SERVER's disk, not the caller's) and SSRF-guard any http(s) it fetches ----
    assert _unsafe_managed_ref({"reference_images": ["data:,x", "https://e/i.png"]}) is None
    for _bad in ("file:///etc/passwd", "/etc/shadow", "~/.ssh/id_rsa", "../s"):
        assert _unsafe_managed_ref({"image": _bad}) == "image", _bad
    os.environ["FAL_KEY"] = "sk"                                   # provider resolves → reach the ref gate
    assert generate_managed("image", "nano-banana",
                            {"prompt": "x", "reference_images": ["file:///etc/passwd"]}
                            )["error"] == "unsafe_reference"       # returns before any provider call
    _clear()
    # an agent-supplied URL fetched server-side (e.g. gemini vision) can't reach metadata / loopback / RFC1918
    for _ssrf in ("http://169.254.169.254/latest/meta-data/", "http://127.0.0.1/", "http://10.0.0.1/"):
        try:
            supercmo_env.safe_fetch_bytes(_ssrf)
            assert False, f"SSRF not blocked: {_ssrf}"
        except ValueError:
            pass

    supercmo_env.reload_keys = _REAL_RELOAD_KEYS
    print("client OK")
