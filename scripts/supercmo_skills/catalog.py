"""Image model catalog — the gateway routing table (LiteLLM-Router style).

Each entry is a provider-blind **alias** the agent passes (`nano-banana-2`, `gpt-image-2`)
mapped to an **ordered list of provider routes**. The resolver picks the first available
route (BYO key present); else the managed proxy. Today every alias has one `fal` route
(fal is an aggregator hosting the Gemini/xAI/OpenAI/BFL/ByteDance models). Adding a direct
provider later = add a `providers/<name>.py` and append a route here — no agent/binding change.

A route carries that provider's own ids + params: fal needs `id` (text-to-image endpoint),
`edit_id` (image-to-image), `max_refs`, `size_style`, `sizes`, `defaults`, `supports`.

The catalog is bundled.
"""

# Video exposes just the two standard video ratios (like image exposes a fixed set) — every model
# supports both. A resolution-tier set; duration is a per-model integer (seconds), validated per route.
VIDEO_ASPECTS = ["16:9", "9:16"]
VIDEO_RESOLUTIONS = ["480p", "720p", "1080p", "4k"]
DEFAULT_MODEL = "nano-banana-2"

# Image exposes explicit ratio strings + a resolution tier (video keeps the named set above).
IMAGE_ASPECTS = ["1:1", "16:9", "9:16", "4:3", "3:4"]
IMAGE_DEFAULT_ASPECT = "1:1"
IMAGE_RESOLUTIONS = ["1k", "2k", "4k"]
IMAGE_DEFAULT_RESOLUTION = "1k"

# image route `sizes` are keyed by the ratio string the tool passes.
_RATIO = {r: r for r in IMAGE_ASPECTS}          # nano-banana / grok (fal takes the ratio string directly)
_PRESET = {"1:1": "square_hd", "16:9": "landscape_16_9", "9:16": "portrait_16_9",
           "4:3": "landscape_4_3", "3:4": "portrait_4_3"}   # seedream / flux / gpt-image-2 (fal presets)


def _fal(id, edit_id, max_refs, size_style, sizes, defaults, supports):
    """Build a fal route (the only provider today)."""
    return {"provider": "fal", "id": id, "edit_id": edit_id, "max_refs": max_refs,
            "size_style": size_style, "sizes": sizes, "defaults": defaults, "supports": supports}


# alias -> { agent-facing metadata, routes: [ordered provider routes] }
IMAGE_MODELS = {
    "nano-banana": {
        "display": "Nano Banana (Gemini 2.5 Flash Image)",
        "strengths": "versatile general-purpose generation, stylized art and illustration",
        "price": "$0.039/image",
        "routes": [_fal(
            "fal-ai/nano-banana", "fal-ai/nano-banana/edit", 4, "aspect_ratio", _RATIO,
            {"num_images": 1, "output_format": "png", "safety_tolerance": "4"},
            {"prompt", "image_urls", "num_images", "seed", "aspect_ratio", "output_format",
             "safety_tolerance", "sync_mode", "limit_generations"})],
    },
    "nano-banana-2": {
        "display": "Nano Banana 2 (Gemini 3.1 Flash Image)",
        "strengths": "stylized art, cartoon and illustration, accurate multilingual text, character consistency",
        "price": "$0.08/image (1K)",
        "routes": [_fal(
            "fal-ai/nano-banana-2", "fal-ai/nano-banana-2/edit", 4, "aspect_ratio", _RATIO,
            {"num_images": 1, "output_format": "png", "resolution": "1K", "safety_tolerance": "4"},
            {"prompt", "image_urls", "aspect_ratio", "num_images", "output_format", "resolution",
             "safety_tolerance", "seed", "sync_mode", "enable_web_search", "limit_generations"})],
    },
    "nano-banana-pro": {
        "display": "Nano Banana Pro (Gemini 3 Pro Image)",
        "strengths": "photorealistic portraits and people (UGC, fashion, editorial); strong text rendering for logos, typography and posters; reasoning depth",
        "price": "$0.15/image (1K)",
        "routes": [_fal(
            "fal-ai/nano-banana-pro", "fal-ai/nano-banana-pro/edit", 4, "aspect_ratio", _RATIO,
            {"num_images": 1, "output_format": "png", "safety_tolerance": "5", "resolution": "1K"},
            {"prompt", "image_urls", "aspect_ratio", "num_images", "output_format", "safety_tolerance",
             "seed", "sync_mode", "resolution", "enable_web_search", "limit_generations"})],
    },
    "grok-imagine": {
        "display": "Grok Imagine Image (xAI)",
        "strengths": "fast, low-cost drafts and quick exploration", "price": "$0.02/image",
        "routes": [_fal(
            "xai/grok-imagine-image", "xai/grok-imagine-image/edit", 3, "aspect_ratio", _RATIO,
            {"num_images": 1, "resolution": "1k", "output_format": "jpeg"},
            {"prompt", "image_urls", "num_images", "aspect_ratio", "resolution", "output_format", "sync_mode"})],
    },
    "seedream-4.5": {
        "display": "Seedream 4.5 (ByteDance)",
        "strengths": "high-resolution photorealism, cinematic stills, reference-driven photo edits",
        "price": "$0.04/image",
        "routes": [_fal(
            "fal-ai/bytedance/seedream/v4.5/text-to-image", "fal-ai/bytedance/seedream/v4.5/edit", 10,
            "image_size_preset", _PRESET, {"num_images": 1},
            {"prompt", "image_urls", "image_size", "num_images", "max_images", "seed",
             "sync_mode", "enable_safety_checker"})],
    },
    "gpt-image-2": {
        "display": "GPT Image 2 (OpenAI)",
        "strengths": "text rendering and CJK for logos, typography, posters, ads and e-commerce packshots; world-aware photorealism",
        "price": "$0.053/image (medium, 1024)",
        "routes": [_fal(
            "fal-ai/gpt-image-2", "openai/gpt-image-2/edit", 16, "image_size_preset", _PRESET,
            {"quality": "medium", "num_images": 1, "output_format": "png"},
            {"prompt", "image_urls", "image_size", "quality", "num_images", "output_format", "sync_mode"})],
    },
    "flux-2-klein-4b": {
        "display": "FLUX.2 Klein 4B (Black Forest Labs)",
        "strengths": "fast, low-cost drafts and quick exploration", "price": "$0.005/MP",
        "routes": [_fal(
            "fal-ai/flux-2/klein/4b", "fal-ai/flux-2/klein/4b/edit", 4, "image_size_preset", _PRESET,
            {"num_inference_steps": 4, "num_images": 1, "output_format": "png"},
            {"prompt", "image_urls", "seed", "num_inference_steps", "image_size", "num_images",
             "sync_mode", "enable_safety_checker", "output_format"})],
    },
    "flux-2-pro": {
        "display": "FLUX.2 Pro (Black Forest Labs)",
        "strengths": "studio photorealism for human portraits, UGC and fashion, and cinematic stills",
        "price": "$0.03/MP",
        "routes": [_fal(
            "fal-ai/flux-2-pro", "fal-ai/flux-2-pro/edit", 4, "image_size_preset", _PRESET,
            {"num_inference_steps": 50, "guidance_scale": 4.5, "num_images": 1,
             "output_format": "png", "safety_tolerance": "5", "sync_mode": True},
            {"prompt", "image_urls", "image_size", "num_inference_steps", "guidance_scale", "num_images",
             "output_format", "enable_safety_checker", "safety_tolerance", "sync_mode", "seed"})],
    },
}


# --- direct vendor routes (BYOK): the video/audio/extract/analysis tables below use _route. ---
def _route(provider, vid, **fields):
    """Generic route: provider name + that vendor's own model-id + per-vendor fields."""
    return {"provider": provider, "id": vid, **fields}


# Video routes: all on the fal queue (bytedance / kling / veo / grok / gemini / wan). Real signatures
# from fal /api docs. A model is a SET of endpoints (text-to-video / image-to-video / first-last-frame /
# reference-to-video), each accepting different media — because fal splits media across endpoints (Veo's
# end frame is a separate `first-last-frame-to-video` endpoint; Seedance's references are a separate
# `reference-to-video` endpoint). The client picks the endpoint whose accepted media-kinds cover exactly
# what the caller supplied, so frame-pins and references (different endpoints) can't be combined.
def _ep(id, media=None, aspects=(), durations=(), resolutions=(), requires=()):
    """One fal endpoint: its id, the media kinds it accepts (tool field -> fal param name, where a
    `*_urls` param is a list and a `*_url` param is a single value), the aspect / duration / resolution
    values valid ON THIS endpoint (empty = no such control), and `requires` — media kinds this endpoint
    demands (e.g. Kling image-to-video always needs a start frame, even when using references)."""
    return {"id": id, "media": dict(media or {}), "aspects": list(aspects),
            "durations": list(durations), "resolutions": list(resolutions), "requires": tuple(requires)}


def _vroute(audio_param=None, duration_unit=None, max_refs=None, combined_ref_max=None,
            defaults=None, **endpoints):
    """One model's fal route: its endpoints (as t2v/i2v/flf/r2v kwargs) plus model-wide fields —
    `audio_param` (fal's audio-toggle name, or None for native/no-audio), `duration_unit` ("s" for
    veo's "8s"), `max_refs` per reference kind, `combined_ref_max` (a shared budget across reference
    images + videos, e.g. Kling's 3 elements / Wan's 5), and `defaults` (fixed per-model params)."""
    return {"provider": "fal", "queued": True, "audio_param": audio_param,
            "duration_unit": duration_unit, "max_refs": dict(max_refs or {}),
            "combined_ref_max": combined_ref_max,
            "defaults": dict(defaults or {}), "endpoints": endpoints}


# --- family builders: one per vendor pipeline (variants differ only by id prefix / a few values). ---
# Every model advertises the same two ratios (VIDEO_ASPECTS); endpoints that derive aspect from the
# input frame (Kling and Wan image-to-video) simply carry no aspect list and ignore it.
def _seedance(prefix, resolutions):
    a, d = VIDEO_ASPECTS, list(range(4, 16))
    return _vroute(audio_param="generate_audio",
        max_refs={"reference_images": 9, "reference_videos": 3, "reference_audios": 3},
        t2v=_ep(f"{prefix}/text-to-video", aspects=a, durations=d, resolutions=resolutions),
        i2v=_ep(f"{prefix}/image-to-video",
            media={"start_frame_image": "image_url", "end_frame_image": "end_image_url"},
            aspects=a, durations=d, resolutions=resolutions),
        r2v=_ep(f"{prefix}/reference-to-video",
            media={"reference_images": "image_urls", "reference_videos": "video_urls",
                   "reference_audios": "audio_urls"},
            aspects=a, durations=d, resolutions=resolutions))


def _kling(prefix, durations):
    # Kling references are `elements` (character/object refs, @Element1) — image sets or videos. They work
    # ONLY on the image-to-video endpoint, which ALWAYS requires a start frame — so on Kling references
    # must accompany a start frame (there is no reference-only mode). Text-to-video is text-only (no
    # elements). Official Kling API: at most 3 elements (images + videos) per task.
    return _vroute(audio_param="generate_audio", combined_ref_max=3,
        max_refs={"reference_images": 3, "reference_videos": 3},
        t2v=_ep(f"{prefix}/text-to-video", aspects=VIDEO_ASPECTS, durations=durations),
        i2v=_ep(f"{prefix}/image-to-video",
            media={"start_frame_image": "start_image_url", "end_frame_image": "end_image_url",
                   "reference_images": "elements", "reference_videos": "elements"},
            durations=durations, requires=("start_frame_image",)))  # i2v always needs a start frame


def _veo(prefix, resolutions):
    a, d = VIDEO_ASPECTS, [4, 6, 8]
    # Google (Ingredients-to-Video): up to 3 reference images.
    return _vroute(audio_param="generate_audio", duration_unit="s", max_refs={"reference_images": 3},
        t2v=_ep(prefix, aspects=a, durations=d, resolutions=resolutions),
        i2v=_ep(f"{prefix}/image-to-video", media={"start_frame_image": "image_url"},
                aspects=a, durations=d, resolutions=resolutions),
        flf=_ep(f"{prefix}/first-last-frame-to-video",   # start+end → a distinct fal endpoint
                media={"start_frame_image": "first_frame_url", "end_frame_image": "last_frame_url"},
                aspects=a, durations=d, resolutions=resolutions),
        r2v=_ep(f"{prefix}/reference-to-video", media={"reference_images": "image_urls"},
                aspects=a, durations=d, resolutions=resolutions))


def _one(display, strengths, price, route):
    return {"display": display, "strengths": strengths, "price": price, "routes": [route]}


# alias -> agent-facing metadata + one provider route. Aliases are ours (never the vendors' job ids).
VIDEO_MODELS = {
    "seedance-2.0": _one("Seedance 2.0 (ByteDance)",
        "cinematic default workhorse; native synced audio, real-world physics and camera control; "
        "start+end frame and image/video/audio references", "~$0.30/s at 720p",
        _seedance("bytedance/seedance-2.0", ["480p", "720p", "1080p", "4k"])),
    "seedance-2.0-mini": _one("Seedance 2.0 Mini (ByteDance)",
        "faster, lower-cost Seedance with native audio; 480p/720p only", "see fal.ai/models",
        _seedance("bytedance/seedance-2.0/mini", ["480p", "720p"])),
    "kling-3.0-pro": _one("Kling 3.0 Pro (Kuaishou)",
        "top-tier image-to-video, fluid cinematic motion, native audio; start+end frame and image/video references",
        "see fal.ai/models", _kling("fal-ai/kling-video/v3/pro", list(range(3, 16)))),
    "kling-3.0-standard": _one("Kling 3.0 Standard (Kuaishou)",
        "standard-tier Kling 3.0; native audio; start+end frame and image/video references",
        "see fal.ai/models", _kling("fal-ai/kling-video/v3/standard", list(range(3, 16)))),
    "veo-3.1": _one("Veo 3.1 (Google)",
        "premium cinematic motion, strong prompt adherence, native audio with dialogue and lip-sync; "
        "start frame, start+end frame, and image references", "$0.20/s (+$0.20/s with audio); 4k $0.40/s",
        _veo("fal-ai/veo3.1", ["720p", "1080p", "4k"])),
    "veo-3.1-fast": _one("Veo 3.1 Fast (Google)",
        "faster, cheaper Veo 3.1 with native audio; start / start+end frame and image references",
        "see fal.ai/models", _veo("fal-ai/veo3.1/fast", ["720p", "1080p", "4k"])),
    "veo-3.1-lite": _one("Veo 3.1 Lite (Google)",
        "lightweight Veo 3.1 tier for quick drafts with native audio; start / start+end frame and image references",
        "see fal.ai/models", _veo("fal-ai/veo3.1/lite", ["720p", "1080p"])),
    "grok-imagine-video": _one("Grok Imagine Video (xAI, via fal)",
        "fast, permissive text/image-to-video drafts with native audio; image references and video-to-video edit",
        "~$4.20/min incl. audio",
        _vroute(max_refs={"reference_images": 7, "reference_videos": 1},
            t2v=_ep("xai/grok-imagine-video/text-to-video", aspects=VIDEO_ASPECTS,
                    durations=list(range(1, 16)), resolutions=["480p", "720p"]),
            i2v=_ep("xai/grok-imagine-video/image-to-video", media={"start_frame_image": "image_url"},
                    aspects=VIDEO_ASPECTS, durations=list(range(1, 16)), resolutions=["480p", "720p"]),
            r2v=_ep("xai/grok-imagine-video/reference-to-video",
                    media={"reference_images": "reference_image_urls"}, aspects=VIDEO_ASPECTS,
                    durations=list(range(1, 16)), resolutions=["480p", "720p"]),
            v2v=_ep("xai/grok-imagine-video/edit-video",   # Grok's only video input is edit (transform a clip)
                    media={"reference_videos": "video_url"}, resolutions=["480p", "720p"]))),
    "gemini-omni": _one("Gemini Omni Flash (Google)",
        "fast multimodal generation with strong coherence and character consistency; native audio; "
        "start frame and image references (fixed 720p, no end frame)",
        "see fal.ai/models",
        _vroute(max_refs={"reference_images": 7},   # Google: up to 7 reference images
            t2v=_ep("google/gemini-omni-flash", aspects=VIDEO_ASPECTS, durations=list(range(3, 11))),
            i2v=_ep("google/gemini-omni-flash/image-to-video", media={"start_frame_image": "image_url"},
                    aspects=VIDEO_ASPECTS, durations=list(range(3, 11))),
            r2v=_ep("google/gemini-omni-flash/reference-to-video",
                    media={"reference_images": "image_urls"}, aspects=VIDEO_ASPECTS,
                    durations=list(range(3, 11))))),
    "wan-2.7": _one("Wan 2.7 (Alibaba)",
        "smooth motion and scene fidelity; start+end frame, driving audio, and image/video references",
        "see fal.ai/models",
        # Wan docs: up to 5 references (images + videos combined); driving audio is a single track.
        _vroute(combined_ref_max=5, max_refs={"reference_images": 5, "reference_videos": 5, "reference_audios": 1},
            t2v=_ep("fal-ai/wan/v2.7/text-to-video", aspects=VIDEO_ASPECTS,
                    durations=list(range(2, 16)), resolutions=["720p", "1080p"]),
            i2v=_ep("fal-ai/wan/v2.7/image-to-video",
                    media={"start_frame_image": "image_url", "end_frame_image": "end_image_url",
                           "reference_audios": "audio_url"},
                    durations=list(range(2, 16)), resolutions=["720p", "1080p"]),
            r2v=_ep("fal-ai/wan/v2.7/reference-to-video",
                    media={"reference_images": "reference_image_urls", "reference_videos": "reference_video_urls"},
                    aspects=VIDEO_ASPECTS, durations=list(range(2, 11)), resolutions=["720p", "1080p"]))),
}

# audio: standalone audio deliverables. `type` selects the mode.
AUDIO_TYPES = ["speech"]

# Output container; each provider maps these onto its own format/sample-rate encoding.
AUDIO_FORMATS = ["mp3", "wav", "pcm", "opus"]

# audio models. Vendor model-ids are tunable constants. Voices are account-level, not per-model —
# list_audio_models resolves them from the caller's own account.
# Prices are the conservative ceiling; the effective rate varies by plan.
_EL_SUPPORTS = {"text", "voice", "speed", "stability", "similarity_boost", "style", "format"}

AUDIO_MODELS = {
    "eleven-v3": {
        "display": "Eleven v3 (ElevenLabs)",
        "strengths": "most expressive delivery, character voices, dramatic reads; widest language "
        "coverage (70+); 5,000 characters per request",
        "price": "~$0.20/1K chars",
        "types": ["speech"],
        "routes": [_route("elevenlabs", "eleven_v3", supports=_EL_SUPPORTS)],
    },
    "eleven-multilingual-v2": {
        "display": "Eleven Multilingual v2 (ElevenLabs)",
        "strengths": "most consistent voice across a long read, long-form narration and explainers; "
        "29 languages; 10,000 characters per request",
        "price": "~$0.20/1K chars",
        "types": ["speech"],
        "routes": [_route("elevenlabs", "eleven_multilingual_v2", supports=_EL_SUPPORTS)],
    },
    "eleven-flash-v2.5": {
        "display": "Eleven Flash v2.5 (ElevenLabs)",
        "strengths": "lowest latency (~75ms) and lowest per-character price, for bulk or draft "
        "reads; 32 languages; 40,000 characters per request",
        "price": "~$0.10/1K chars (half the others)",
        "types": ["speech"],
        "routes": [_route("elevenlabs", "eleven_flash_v2_5", supports=_EL_SUPPORTS)],
    },
}

# extraction: structured data (fields + image URLs) from any web/product page via a prompt/schema.
EXTRACT_MODELS = {
    "web-extract": {
        "display": "Web Extract (Firecrawl)",
        "strengths": "structured product/page data and image URLs from any e-commerce or web page, "
        "guided by a prompt or JSON schema",
        "price": "see https://firecrawl.dev/pricing",
        "routes": [_route("firecrawl", "firecrawl-v2", supports={"url", "prompt", "schema"})],
    },
}

# vision: read an image and answer a question about it (category, details, on-pack text, layout).
ANALYSIS_MODELS = {
    "gemini-flash-latest": {
        "display": "Gemini Flash (Google, vision)",
        "strengths": "reads an image or a short video and answers about it — product category, "
        "materials, on-pack text, distinctive details, whether a shot is product-only or shows a "
        "face, and a clip's subject, actions, camera/motion, and audio",
        "price": "see https://ai.google.dev/pricing",
        "routes": [_route("gemini", "gemini-flash-latest", supports={"image", "video", "prompt"})],
    },
}


# capability -> model table. Adding a capability = one entry here + a table above.
_TABLES = {"image": IMAGE_MODELS, "video": VIDEO_MODELS, "audio": AUDIO_MODELS,
           "extract": EXTRACT_MODELS, "analysis": ANALYSIS_MODELS}
DEFAULTS = {"image": DEFAULT_MODEL, "video": "seedance-2.0", "audio": "eleven-v3",
            "extract": "web-extract", "analysis": "gemini-flash-latest"}


def get(capability, model):
    """Catalog entry for (capability, model), or None."""
    return (_TABLES.get(capability) or {}).get(model)


def routes_of(capability, model):
    """Ordered provider routes for (capability, model) (priority order); [] if unknown."""
    return ((_TABLES.get(capability) or {}).get(model) or {}).get("routes", [])


def default_model(capability):
    """The default alias for a capability (used when the agent omits `model`)."""
    return DEFAULTS.get(capability)


def image_models_listing(query=None):
    """Discovery payload for list_image_models: default model + the valid aspect ratios and
    resolution tiers image_generate accepts + the models (optionally filtered by `query`)."""
    return {"ok": True, "default": DEFAULT_MODEL, "aspect_ratios": IMAGE_ASPECTS,
            "resolutions": IMAGE_RESOLUTIONS, "models": list_models("image", query)}


_REF_KINDS = ("reference_images", "reference_videos", "reference_audios")


def video_media_kinds(route):
    """Every media kind any endpoint of this model accepts (for discovery + error messages)."""
    kinds = set()
    for ep in route["endpoints"].values():
        kinds |= set(ep["media"])
    return kinds


def video_endpoint_for(route, populated):
    """The endpoint whose accepted media-kinds cover `populated` (a set of tool media-field names),
    choosing the most specific (fewest media keys). None when no single endpoint accepts that
    combination — e.g. a start frame together with references (they live on different endpoints)."""
    covering = [ep for ep in route["endpoints"].values() if set(populated) <= set(ep["media"])]
    return min(covering, key=lambda ep: len(ep["media"])) if covering else None


def _video_model_detail(name, meta, route):
    """Full per-model schema for list_video_models (Option B): the values valid across the model's
    endpoints. `media` shows start/end frame support (bool) and each reference kind's max count."""
    aspects, resolutions, durations = [], [], set()
    for ep in route["endpoints"].values():
        aspects += [a for a in ep["aspects"] if a not in aspects]
        resolutions += [r for r in ep["resolutions"] if r not in resolutions]
        durations |= set(ep["durations"])
    kinds = video_media_kinds(route)
    media = {k: True for k in ("start_frame_image", "end_frame_image") if k in kinds}
    media.update({k: route["max_refs"].get(k, True) for k in _REF_KINDS if k in kinds})
    if route.get("combined_ref_max") is not None:
        media["reference_images_videos_combined_max"] = route["combined_ref_max"]
    return {"model": name, "display": meta["display"], "strengths": meta["strengths"],
            "price": meta["price"], "modes": sorted(route["endpoints"].keys()),
            "aspect_ratios": aspects or None, "durations": sorted(durations) or None,
            "resolutions": resolutions or None, "media": media, "audio": bool(route["audio_param"])}


def video_models_listing(query=None):
    """Discovery payload for list_video_models (Option B): the default model + the full per-model schema
    for all matching models — each model's modes, aspect ratios, durations, resolutions, accepted media
    (start/end frame + reference kinds with max counts), and audio support. This is the authoritative
    source of truth; SKILL.md must not duplicate it."""
    q = (query or "").lower().strip()
    models = []
    for name, meta in VIDEO_MODELS.items():
        if q and q not in f"{name} {meta['display']} {meta['strengths']}".lower():
            continue
        models.append(_video_model_detail(name, meta, meta["routes"][0]))
    return {"ok": True, "default": DEFAULTS["video"], "aspect_ratios": VIDEO_ASPECTS,
            "resolutions": VIDEO_RESOLUTIONS, "models": models}


def list_models(capability, query=None):
    """Agent-facing discovery for a capability: name/display/strengths/price (+types for audio)."""
    q = (query or "").lower().strip()
    out = []
    for name, m in (_TABLES.get(capability) or {}).items():
        if q and q not in f"{name} {m['display']} {m['strengths']}".lower():
            continue
        row = {"model": name, "display": m["display"], "strengths": m["strengths"], "price": m["price"]}
        if "types" in m:
            row["types"] = m["types"]
        out.append(row)
    return out


def audio_models_listing(query=None):
    """Discovery payload for list_audio_models: the default alias, the modes and output formats
    audio_generate accepts, and the matching models. Voices are their own tool (list_voices) —
    they belong to the account, not to a model."""
    return {"ok": True, "default": DEFAULTS["audio"], "types": AUDIO_TYPES,
            "formats": AUDIO_FORMATS, "models": list_models("audio", query),
            "voices_note": "call list_voices to choose a voice — every model accepts any of them"}


if __name__ == "__main__":
    assert routes_of("image", "gpt-image-2")[0]["provider"] == "fal"
    assert routes_of("image", "grok-imagine")[0]["provider"] == "fal"
    assert routes_of("image", "nano-banana")[0]["provider"] == "fal"
    assert default_model("video") == "seedance-2.0"
    assert len(VIDEO_MODELS) == 10
    assert all(routes_of("video", m)[0]["provider"] == "fal" for m in VIDEO_MODELS)
    _sd = routes_of("video", "seedance-2.0")[0]
    assert video_endpoint_for(_sd, set())["id"].endswith("text-to-video")
    assert video_endpoint_for(_sd, {"start_frame_image"})["id"].endswith("image-to-video")
    assert video_endpoint_for(_sd, {"reference_audios"})["id"].endswith("reference-to-video")
    _veo = routes_of("video", "veo-3.1")[0]
    assert video_endpoint_for(_veo, {"start_frame_image"})["id"].endswith("image-to-video")
    assert video_endpoint_for(_veo, {"start_frame_image", "end_frame_image"})["id"].endswith("first-last-frame-to-video")
    assert video_endpoint_for(routes_of("video", "grok-imagine-video")[0], {"start_frame_image", "reference_images"}) is None
    # Kling references ride on the i2v endpoint, so start frame + references CAN combine there
    assert video_endpoint_for(routes_of("video", "kling-3.0-pro")[0], {"start_frame_image", "reference_images"})["id"].endswith("image-to-video")
    assert "reference_videos" not in video_media_kinds(_veo)   # veo has no video references
    assert _video_model_detail("veo-3.1", VIDEO_MODELS["veo-3.1"], _veo)["media"]["end_frame_image"] is True
    assert default_model("audio") == "eleven-v3"
    assert all(routes_of("audio", m)[0]["provider"] == "elevenlabs" for m in AUDIO_MODELS)
    assert routes_of("audio", "eleven-v3")[0]["id"] == "eleven_v3"
    assert list_models("audio")[0]["types"] == ["speech"]
    # voices are account-level: never carried per model, only resolved live
    assert all("voices" not in m for m in list_models("audio"))
    _listing = audio_models_listing()
    assert _listing["default"] == "eleven-v3" and _listing["types"] == AUDIO_TYPES
    assert len(_listing["models"]) == 3
    # voices moved to their own tool — the models payload must not carry them at all
    assert "voices" not in _listing and "list_voices" in _listing["voices_note"]
    assert list_models("audio", "long-form")[0]["model"] == "eleven-multilingual-v2"
    print("catalog OK:", {c: list(t) for c, t in _TABLES.items()})
