"""Image model catalog — the gateway routing table (LiteLLM-Router style).

Each entry is a provider-blind **alias** the agent passes (`nano-banana-2`, `gpt-image-2`)
mapped to an **ordered list of provider routes**. The resolver picks the first available
route (BYO key present); else the managed proxy. Today every alias has one `fal` route
(fal is an aggregator hosting the Gemini/xAI/OpenAI/BFL/ByteDance models). Adding a direct
provider later = add a `providers/<name>.py` and append a route here — no agent/binding change.

A route carries that provider's own ids + params: fal needs `id` (text-to-image endpoint),
`edit_id` (image-to-image), `max_refs`, `size_style`, `sizes`, `defaults`, `supports`.

ponytail: catalog is bundled; when the proxy exposes GET /proxy/catalog, `list_models()` can
fetch+cache it with this as the fallback. No endpoint yet → bundled only.
"""

ASPECTS = ["square", "landscape", "portrait"]     # video aspect set (named)
DEFAULT_ASPECT = "square"
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


# --- direct vendor routes (BYOK): the video/tts/extract/analysis tables below use _route. ---
def _route(provider, vid, **fields):
    """Generic route: provider name + that vendor's own model-id + per-vendor fields."""
    return {"provider": provider, "id": vid, **fields}


# veo3.1 accepts only 'auto' / '16:9' / '9:16' (no 1:1) — map square → auto so the default aspect works.
_VRATIO = {"square": "auto", "landscape": "16:9", "portrait": "9:16"}

# video models (queued routes run on fal's queue host; xai video polls x.ai)
VIDEO_MODELS = {
    "veo3.1-fast": {
        "display": "Veo 3.1 Fast (Google, image-to-video)",
        "strengths": "fast image-to-video with native audio; cinematic motion from a start frame",
        "price": "$0.10/s (no audio), $0.15/s (with audio), 720p",
        "routes": [_route("fal", "fal-ai/veo3.1/fast/image-to-video", queued=True, sizes=_VRATIO,
            duration_unit="s",   # veo wants "8s" not 8 (Hermes video_gen/fal duration_suffix)
            defaults={"duration": 8, "resolution": "720p", "generate_audio": True},
            supports={"prompt", "image_url", "duration", "resolution", "aspect_ratio", "generate_audio", "seed"})],
    },
    "grok-video": {
        "display": "Grok Imagine Video (xAI)",
        "strengths": "fast text/image-to-video drafts",
        "price": "see https://docs.x.ai",
        # i2v uses grok-imagine-video-1.5-preview, t2v uses grok-imagine-video (Hermes video_gen/xai).
        "routes": [_route("xai", "grok-imagine-video", i2v_id="grok-imagine-video-1.5-preview",
                          supports={"prompt", "image_url", "duration"})],
    },
}

# tts models. Vendor model-ids are tunable constants; voices are agent-facing discovery hints.
TTS_MODELS = {
    "elevenlabs-v3": {
        "display": "ElevenLabs (multilingual)",
        "strengths": "highest-quality multilingual speech, large expressive voice library",
        "price": "~$0.05/1K chars",
        "voices": ["Aria", "Rachel", "Roger", "Sarah"],
        "routes": [
            _route("elevenlabs", "eleven_multilingual_v2", supports={"text", "voice", "stability", "speed"}),
            _route("fal", "fal-ai/elevenlabs/tts/eleven-v3", queued=True,
                   defaults={"voice": "Aria"}, supports={"text", "voice", "stability", "speed"})],
    },
    "openai-tts": {
        "display": "OpenAI TTS",
        "strengths": "natural, low-latency narration",
        "price": "~$0.015/1K chars",
        "voices": ["alloy", "nova", "shimmer", "echo"],
        "routes": [_route("openai", "gpt-4o-mini-tts", supports={"input", "voice", "speed"})],
    },
    "gemini-tts": {
        "display": "Gemini TTS",
        "strengths": "expressive, multilingual, controllable style",
        "price": "see https://ai.google.dev",
        "voices": ["Kore", "Puck", "Charon"],
        "routes": [_route("gemini", "gemini-2.5-flash-preview-tts", supports={"text", "voice"})],
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
        "strengths": "reads an image and answers about it — product category, materials, on-pack text, "
        "distinctive details, and whether a shot is product-only or shows a face",
        "price": "see https://ai.google.dev/pricing",
        "routes": [_route("gemini", "gemini-flash-latest", supports={"image", "prompt"})],
    },
}


# capability -> model table. Adding a capability = one entry here + a table above.
_TABLES = {"image": IMAGE_MODELS, "video": VIDEO_MODELS, "tts": TTS_MODELS,
           "extract": EXTRACT_MODELS, "analysis": ANALYSIS_MODELS}
DEFAULTS = {"image": DEFAULT_MODEL, "video": "veo3.1-fast", "tts": "elevenlabs-v3",
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


def list_models(capability, query=None):
    """Agent-facing discovery for a capability: name/display/strengths/price (+voices for tts)."""
    q = (query or "").lower().strip()
    out = []
    for name, m in (_TABLES.get(capability) or {}).items():
        if q and q not in f"{name} {m['display']} {m['strengths']}".lower():
            continue
        row = {"model": name, "display": m["display"], "strengths": m["strengths"], "price": m["price"]}
        if "voices" in m:
            row["voices"] = m["voices"]
        out.append(row)
    return out


if __name__ == "__main__":
    assert routes_of("image", "gpt-image-2")[0]["provider"] == "fal"
    assert routes_of("image", "grok-imagine")[0]["provider"] == "fal"
    assert routes_of("image", "nano-banana")[0]["provider"] == "fal"
    assert routes_of("video", "veo3.1-fast")[0].get("queued") is True
    assert routes_of("video", "grok-video")[0]["provider"] == "xai"
    assert default_model("tts") == "elevenlabs-v3"
    assert list_models("tts")[0].get("voices")
    print("catalog OK:", {c: list(t) for c, t in _TABLES.items()})
