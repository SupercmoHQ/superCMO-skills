"""Image model catalog — the gateway routing table (LiteLLM-Router style).

Each entry is a provider-blind **alias** the agent passes (`nano-banana-2`, `gpt-image-2`)
mapped to an **ordered list of provider routes**. The resolver picks the first available
route (BYO key present); else the managed proxy.

Every image/video alias carries two routes, `wavespeed` then `fal` — both aggregators hosting the
Gemini/xAI/OpenAI/BFL/ByteDance/Kuaishou/Alibaba models. The first one whose key is set serves the
call; `SUPERCMO_MEDIA_PROVIDER=fal|wavespeed` pins one when both are. Adding a direct provider later
= add a `providers/<name>.py` and append a route here — no agent/binding change.

A route carries that provider's own ids + params: `id` (text-to-image endpoint), `edit_id`
(image-to-image), `max_refs`, `size_style`, `sizes`, `defaults`, `supports`, and its own `price`,
since the two providers bill differently.

The routes of an alias are kept at PARITY: a capability one provider cannot serve is carried by
neither, so an alias means the same thing whichever route runs it.

The catalog is bundled.
"""

# Video exposes just the two standard video ratios (like image exposes a fixed set) — every model
# supports both. A resolution-tier set; duration is a per-model integer (seconds), validated per route.
VIDEO_ASPECTS = ["16:9", "9:16"]
VIDEO_RESOLUTIONS = ["480p", "720p", "1080p", "4k"]
DEFAULT_MODEL = "nano-banana-2"

# Image exposes explicit ratio strings + a resolution tier (video keeps the named set above).
# Aspect support is per-model: a route's `sizes` map is the authority on what that model accepts.
IMAGE_ASPECTS_COMMON = ["1:1", "16:9", "9:16", "4:3", "3:4"]   # every image model
_GEMINI_PRO_EXTRA = ["4:5", "21:9"]                            # Gemini 3 Pro Image only
IMAGE_ASPECTS = IMAGE_ASPECTS_COMMON + _GEMINI_PRO_EXTRA       # the union the tool's enum accepts
IMAGE_DEFAULT_ASPECT = "1:1"
IMAGE_RESOLUTIONS = ["1k", "2k", "4k"]
IMAGE_DEFAULT_RESOLUTION = "1k"

# image route `sizes` are keyed by the ratio string the tool passes.
_RATIO = {r: r for r in IMAGE_ASPECTS_COMMON}   # nano-banana / grok (fal takes the ratio string directly)
_RATIO_PRO = {r: r for r in IMAGE_ASPECTS}      # nano-banana-pro also takes 4:5 and 21:9
_PRESET = {"1:1": "square_hd", "16:9": "landscape_16_9", "9:16": "portrait_16_9",
           "4:3": "landscape_4_3", "3:4": "portrait_4_3"}   # seedream / flux / gpt-image-2 (fal presets)

# WaveSpeed takes the ratio string directly on every image model except FLUX, which takes a
# `size` of "width*height" — so FLUX's `sizes` map holds pixel strings (~1MP at each ratio).
_WS_RATIO_ALL = {r: r for r in IMAGE_ASPECTS}          # gemini pro / seedream / gpt-image-2
_WS_RATIO_5 = {r: r for r in IMAGE_ASPECTS_COMMON}     # grok: no 4:5 and no 21:9
_WS_SIZE = {"1:1": "1024*1024", "16:9": "1344*768", "9:16": "768*1344", "4:3": "1152*896",
            "3:4": "896*1152", "4:5": "896*1120", "21:9": "1536*640"}


def _fal(id, edit_id, max_refs, size_style, sizes, defaults, supports, price):
    """Build a fal image route."""
    return {"provider": "fal", "id": id, "edit_id": edit_id, "max_refs": max_refs,
            "size_style": size_style, "sizes": sizes, "defaults": defaults, "supports": supports,
            "price": price}


def _ws(id, edit_id, max_refs, size_style, sizes, defaults, supports, price,
        edit_supports=None, resolutions=None, ref_param="images", ref_scalar=False):
    """Build a WaveSpeed image route. Two fields fal doesn't need: `edit_supports`, because
    WaveSpeed's edit endpoint often accepts FEWER params than its text-to-image twin (grok's edit
    takes only prompt+image; FLUX's edit has no `size`), and `resolutions`, the tiers this model
    actually bills — an unsupported tier is dropped rather than sent and 422'd."""
    return {"provider": "wavespeed", "id": id, "edit_id": edit_id, "max_refs": max_refs,
            "size_style": size_style, "sizes": sizes, "defaults": defaults, "supports": supports,
            "edit_supports": edit_supports, "resolutions": list(resolutions or []),
            "ref_param": ref_param, "ref_scalar": ref_scalar, "price": price}


# alias -> { agent-facing metadata, routes: [wavespeed, fal] }. `price` lives on each route.
IMAGE_MODELS = {
    "nano-banana": {
        "display": "Nano Banana (Gemini 2.5 Flash Image)",
        "strengths": "versatile general-purpose generation, stylized art and illustration",
        "routes": [_ws(
            "google/nano-banana/text-to-image", "google/nano-banana/edit", 10, "aspect_ratio",
            _WS_RATIO_ALL, {"output_format": "png"},
            {"prompt", "images", "aspect_ratio", "output_format"},   # no resolution tier on v1
            "$0.039/image"),
            _fal(
            "fal-ai/nano-banana", "fal-ai/nano-banana/edit", 4, "aspect_ratio", _RATIO,
            {"num_images": 1, "output_format": "png", "safety_tolerance": "4"},
            {"prompt", "image_urls", "num_images", "seed", "aspect_ratio", "output_format",
             "safety_tolerance", "sync_mode", "limit_generations"}, "$0.039/image")],
    },
    "nano-banana-2": {
        "display": "Nano Banana 2 (Gemini 3.1 Flash Image)",
        "strengths": "stylized art, cartoon and illustration, accurate multilingual text, character consistency",
        "routes": [_ws(
            "google/nano-banana-2/text-to-image", "google/nano-banana-2/edit", 14, "aspect_ratio",
            _WS_RATIO_ALL, {"output_format": "png"},
            {"prompt", "images", "aspect_ratio", "resolution", "output_format",
             "enable_web_search", "enable_image_search"},
            "$0.07/image (1k); $0.105 2k, $0.14 4k", resolutions=["0.5k", "1k", "2k", "4k"]),
            _fal(
            "fal-ai/nano-banana-2", "fal-ai/nano-banana-2/edit", 4, "aspect_ratio", _RATIO,
            {"num_images": 1, "output_format": "png", "resolution": "1K", "safety_tolerance": "4"},
            {"prompt", "image_urls", "aspect_ratio", "num_images", "output_format", "resolution",
             "safety_tolerance", "seed", "sync_mode", "enable_web_search", "limit_generations"},
            "$0.08/image (1K)")],
    },
    "nano-banana-pro": {
        "display": "Nano Banana Pro (Gemini 3 Pro Image)",
        "strengths": "photorealistic portraits and people (UGC, fashion, editorial); strong text rendering for logos, typography and posters; reasoning depth",
        "routes": [_ws(
            "google/nano-banana-pro/text-to-image", "google/nano-banana-pro/edit", 14, "aspect_ratio",
            _WS_RATIO_ALL, {"output_format": "png"},
            {"prompt", "images", "aspect_ratio", "resolution", "output_format"},
            "$0.14/image (1k and 2k); $0.24 4k", resolutions=["1k", "2k", "4k"]),
            _fal(
            "fal-ai/nano-banana-pro", "fal-ai/nano-banana-pro/edit", 4, "aspect_ratio", _RATIO_PRO,
            {"num_images": 1, "output_format": "png", "safety_tolerance": "5", "resolution": "1K"},
            {"prompt", "image_urls", "aspect_ratio", "num_images", "output_format", "safety_tolerance",
             "seed", "sync_mode", "resolution", "enable_web_search", "limit_generations"},
            "$0.15/image (1K)")],
    },
    "grok-imagine": {
        "display": "Grok Imagine Image (xAI)",
        "strengths": "fast, low-cost drafts and quick exploration",
        # WaveSpeed's grok edit takes ONE image and nothing but a prompt beside it — hence
        # ref_scalar + the narrower edit_supports.
        "routes": [_ws(
            "x-ai/grok-imagine-image/text-to-image", "x-ai/grok-imagine-image/edit", 1,
            "aspect_ratio", _WS_RATIO_5, {"output_format": "jpeg"},
            {"prompt", "aspect_ratio", "output_format"}, "$0.022/image ($0.025 edit)",
            edit_supports={"prompt", "image"}, ref_param="image", ref_scalar=True),
            _fal(
            "xai/grok-imagine-image", "xai/grok-imagine-image/edit", 3, "aspect_ratio", _RATIO,
            {"num_images": 1, "resolution": "1k", "output_format": "jpeg"},
            {"prompt", "image_urls", "num_images", "aspect_ratio", "resolution", "output_format",
             "sync_mode"}, "$0.02/image")],
    },
    "seedream-5": {
        "display": "Seedream 5 Pro (ByteDance)",
        "strengths": "high-resolution photorealism, cinematic stills, reference-driven photo edits",
        "routes": [_ws(
            "bytedance/seedream-v5.0-pro", "bytedance/seedream-v5.0-pro/edit", 10, "aspect_ratio",
            _WS_RATIO_ALL, {"output_format": "png"},
            {"prompt", "images", "aspect_ratio", "resolution", "output_format"},
            "$0.045/image (1k, 1.5k); $0.090 2k, +$0.003 per extra input image",
            resolutions=["1k", "1.5k", "2k"]),           # no 4k tier — a 4k ask falls back to 2k
            _fal(
            "bytedance/seedream/v5/pro/text-to-image", "bytedance/seedream/v5/pro/edit", 10,
            "image_size_preset", _PRESET, {"num_images": 1},
            {"prompt", "image_urls", "image_size", "num_images", "max_images", "seed",
             "sync_mode", "enable_safety_checker"},
            "$0.0675/image (up to 1536px); $0.135 up to 2048px")],
    },
    "gpt-image-2": {
        "display": "GPT Image 2 (OpenAI)",
        "strengths": "text rendering and CJK for logos, typography, posters, ads and e-commerce packshots; world-aware photorealism",
        "routes": [_ws(
            "openai/gpt-image-2/text-to-image", "openai/gpt-image-2/edit", 16, "aspect_ratio",
            _WS_RATIO_ALL, {"quality": "medium", "output_format": "png"},
            {"prompt", "images", "aspect_ratio", "resolution", "quality", "output_format"},
            "$0.06/image (medium, 1k); $0.10 2k, $0.18 4k", resolutions=["1k", "2k", "4k"]),
            _fal(
            "fal-ai/gpt-image-2", "openai/gpt-image-2/edit", 16, "image_size_preset", _PRESET,
            {"quality": "medium", "num_images": 1, "output_format": "png"},
            {"prompt", "image_urls", "image_size", "quality", "num_images", "output_format",
             "sync_mode"}, "$0.053/image (medium, 1024)")],
    },
    "flux-2-klein-4b": {
        "display": "FLUX.2 Klein 4B (Black Forest Labs)",
        "strengths": "fast, low-cost drafts and quick exploration",
        # FLUX sizes are pixels, not ratios; and its edit endpoint has no size at all — the output
        # matches the input image, so edit_supports drops it rather than 422-ing.
        "routes": [_ws(
            "wavespeed-ai/flux-2-klein-4b/text-to-image", "wavespeed-ai/flux-2-klein-4b/edit", 3,
            "size_wh", _WS_SIZE, {}, {"prompt", "size", "seed"}, "$0.008/image ($0.012 edit)",
            edit_supports={"prompt", "images", "seed"}),
            _fal(
            "fal-ai/flux-2/klein/4b", "fal-ai/flux-2/klein/4b/edit", 4, "image_size_preset", _PRESET,
            {"num_inference_steps": 4, "num_images": 1, "output_format": "png"},
            {"prompt", "image_urls", "seed", "num_inference_steps", "image_size", "num_images",
             "sync_mode", "enable_safety_checker", "output_format"}, "$0.005/MP")],
    },
    "flux-2-pro": {
        "display": "FLUX.2 Pro (Black Forest Labs)",
        "strengths": "studio photorealism for human portraits, UGC and fashion, and cinematic stills",
        "routes": [_ws(
            "wavespeed-ai/flux-2-pro/text-to-image", "wavespeed-ai/flux-2-pro/edit", 3,
            "size_wh", _WS_SIZE, {}, {"prompt", "size", "seed"}, "$0.03/image",
            edit_supports={"prompt", "images", "seed"}),
            _fal(
            "fal-ai/flux-2-pro", "fal-ai/flux-2-pro/edit", 4, "image_size_preset", _PRESET,
            {"num_inference_steps": 50, "guidance_scale": 4.5, "num_images": 1,
             "output_format": "png", "safety_tolerance": "5", "sync_mode": True},
            {"prompt", "image_urls", "image_size", "num_inference_steps", "guidance_scale", "num_images",
             "output_format", "enable_safety_checker", "safety_tolerance", "sync_mode", "seed"},
            "$0.03/MP")],
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


def _ws_ep(id, media=None, media_scalar=(), aspects=(), durations=(), resolutions=(), requires=()):
    """One WaveSpeed endpoint. Same shape as `_ep` plus `media_scalar` — the set of params that take
    a single value rather than a list. fal encodes that in the param NAME (`*_urls` vs `*_url`);
    WaveSpeed doesn't (Wan's `videos` is a list, Grok's `video` is scalar), so it's declared."""
    return {"id": id, "media": dict(media or {}), "media_scalar": tuple(media_scalar),
            "aspects": list(aspects), "durations": list(durations),
            "resolutions": list(resolutions), "requires": tuple(requires)}


def _ws_vroute(price, audio_param=None, max_refs=None, combined_ref_max=None, defaults=None,
               **endpoints):
    """One model's WaveSpeed route. No `duration_unit` — WaveSpeed takes plain integer seconds
    everywhere (fal needs veo's "8s")."""
    return {"provider": "wavespeed", "queued": True, "audio_param": audio_param,
            "duration_unit": None, "max_refs": dict(max_refs or {}),
            "combined_ref_max": combined_ref_max, "price": price,
            "defaults": dict(defaults or {}), "endpoints": endpoints}


def _vroute(audio_param=None, duration_unit=None, max_refs=None, combined_ref_max=None,
            defaults=None, price=None, **endpoints):
    """One model's fal route: its endpoints (as t2v/i2v/flf/r2v kwargs) plus model-wide fields —
    `audio_param` (fal's audio-toggle name, or None for native/no-audio), `duration_unit` ("s" for
    veo's "8s"), `max_refs` per reference kind, `combined_ref_max` (a shared budget across reference
    images + videos, e.g. Kling's 3 elements / Wan's 5), and `defaults` (fixed per-model params)."""
    return {"provider": "fal", "queued": True, "audio_param": audio_param,
            "duration_unit": duration_unit, "max_refs": dict(max_refs or {}),
            "combined_ref_max": combined_ref_max, "price": price,
            "defaults": dict(defaults or {}), "endpoints": endpoints}


# --- family builders: one per vendor pipeline (variants differ only by id prefix / a few values). ---
# Every model advertises the same two ratios (VIDEO_ASPECTS); endpoints that derive aspect from the
# input frame (Kling, Wan and Seedance 2.5 image-to-video) simply carry no aspect list and ignore it.
# Seedance's two generations share a shape but not their numbers: 2.5 doubles the clip ceiling to
# 30s, lifts the reference ceiling to 50 files, and takes no `aspect_ratio` on image-to-video —
# fal's accepts only "auto" there, WaveSpeed has no such param at all — hence `i2v_aspect=False`.
_SD_DURATIONS = list(range(4, 16))                 # 2.0 / fast / mini
_SD25_DURATIONS = list(range(4, 31))               # 2.5: one continuous take up to 30s
_SD_REFS = {"reference_images": 9, "reference_videos": 3, "reference_audios": 3}
_SD25_REFS = {"reference_images": 30, "reference_videos": 10, "reference_audios": 10}


def _seedance(prefix, resolutions, price=None, durations=None, max_refs=None, i2v_aspect=True):
    a, d = VIDEO_ASPECTS, durations or _SD_DURATIONS
    return _vroute(audio_param="generate_audio", price=price, max_refs=max_refs or _SD_REFS,
        t2v=_ep(f"{prefix}/text-to-video", aspects=a, durations=d, resolutions=resolutions),
        i2v=_ep(f"{prefix}/image-to-video",
            media={"start_frame_image": "image_url", "end_frame_image": "end_image_url"},
            aspects=a if i2v_aspect else [], durations=d, resolutions=resolutions),
        r2v=_ep(f"{prefix}/reference-to-video",
            media={"reference_images": "image_urls", "reference_videos": "video_urls",
                   "reference_audios": "audio_urls"},
            aspects=a, durations=d, resolutions=resolutions))


def _kling(prefix, durations, price=None):
    # PARITY: Kling carries NO references on either lane. fal would accept them as `elements` (image
    # sets or videos on the image-to-video endpoint), but WaveSpeed's Kling takes references only as
    # `element_list` — pre-created Element IDs from a separate billed kling-elements call — and takes
    # no video input at all. Advertising them here would mean a video that silently loses its
    # references the moment a user switches lanes, so Kling is frames-only for both.
    return _vroute(audio_param="generate_audio", price=price,
        t2v=_ep(f"{prefix}/text-to-video", aspects=VIDEO_ASPECTS, durations=durations),
        i2v=_ep(f"{prefix}/image-to-video",
            media={"start_frame_image": "start_image_url", "end_frame_image": "end_image_url"},
            durations=durations, requires=("start_frame_image",)))  # i2v always needs a start frame


def _veo(prefix, resolutions, price=None, references=True):
    a, d = VIDEO_ASPECTS, [4, 6, 8]
    # Google (Ingredients-to-Video): up to 3 reference images. PARITY: the `lite` tier passes
    # references=False — fal serves veo3.1/lite/reference-to-video but WaveSpeed has no lite
    # reference endpoint, so neither lane advertises one.
    eps = dict(
        t2v=_ep(prefix, aspects=a, durations=d, resolutions=resolutions),
        i2v=_ep(f"{prefix}/image-to-video", media={"start_frame_image": "image_url"},
                aspects=a, durations=d, resolutions=resolutions),
        flf=_ep(f"{prefix}/first-last-frame-to-video",   # start+end → a distinct fal endpoint
                media={"start_frame_image": "first_frame_url", "end_frame_image": "last_frame_url"},
                aspects=a, durations=d, resolutions=resolutions))
    if references:
        eps["r2v"] = _ep(f"{prefix}/reference-to-video", media={"reference_images": "image_urls"},
                         aspects=a, durations=d, resolutions=resolutions)
    return _vroute(audio_param="generate_audio", duration_unit="s", price=price,
        max_refs={"reference_images": 3} if references else {}, **eps)


# --- WaveSpeed family builders. Two structural differences from the fal side worth knowing:
#     * Seedance's references live ON text-to-video, not a separate reference-to-video endpoint.
#     * Veo's first-last-frame folds into image-to-video via `last_image` (except lite, which keeps
#       a distinct start-end-to-video). So a WaveSpeed model has FEWER endpoints for the same reach.
_WS_FRAMES = {"start_frame_image": "image", "end_frame_image": "last_image"}
_WS_FRAME_SCALAR = ("image", "last_image")


def _ws_seedance(prefix, price, durations=None, max_refs=None, i2v_aspect=True):
    a, d, r = VIDEO_ASPECTS, durations or _SD_DURATIONS, ["480p", "720p", "1080p", "4k"]
    return _ws_vroute(price, audio_param="generate_audio", max_refs=max_refs or _SD_REFS,
        t2v=_ws_ep(f"{prefix}/text-to-video",
            media={"reference_images": "reference_images", "reference_videos": "reference_videos",
                   "reference_audios": "reference_audios"},
            aspects=a, durations=d, resolutions=r),
        i2v=_ws_ep(f"{prefix}/image-to-video", media=_WS_FRAMES, media_scalar=_WS_FRAME_SCALAR,
            aspects=a if i2v_aspect else [], durations=d, resolutions=r,
            requires=("start_frame_image",)))


def _ws_kling(prefix, price):
    # Kling's audio toggle is `sound`, its end frame is `end_image`, and it carries NO references on
    # this lane: its only reference path is `element_list` (pre-created Element IDs from a separate
    # billed kling-elements call), and it accepts no video input at all. Frames-only, both lanes.
    d = list(range(3, 16))
    return _ws_vroute(price, audio_param="sound",
        t2v=_ws_ep(f"{prefix}/text-to-video", aspects=VIDEO_ASPECTS, durations=d),
        i2v=_ws_ep(f"{prefix}/image-to-video",
            media={"start_frame_image": "image", "end_frame_image": "end_image"},
            media_scalar=("image", "end_image"), durations=d, requires=("start_frame_image",)))


def _ws_veo(prefix, resolutions, price):
    a, d = VIDEO_ASPECTS, [4, 6, 8]
    return _ws_vroute(price, audio_param="generate_audio", max_refs={"reference_images": 3},
        t2v=_ws_ep(f"{prefix}/text-to-video", aspects=a, durations=d, resolutions=resolutions),
        i2v=_ws_ep(f"{prefix}/image-to-video", media=_WS_FRAMES, media_scalar=_WS_FRAME_SCALAR,
            aspects=a, durations=d, resolutions=resolutions, requires=("start_frame_image",)),
        r2v=_ws_ep(f"{prefix}/reference-to-video", media={"reference_images": "images"},
            aspects=a, resolutions=resolutions))   # no duration control on reference-to-video


def _one(display, strengths, route, *more):
    """One alias: agent-facing metadata plus its ordered routes (wavespeed first, then fal)."""
    return {"display": display, "strengths": strengths, "routes": [route, *more]}


# alias -> agent-facing metadata + [wavespeed route, fal route]. Aliases are ours (never a vendor's).
VIDEO_MODELS = {
    "seedance-2.5": _one("Seedance 2.5 (ByteDance)",
        "one continuous take up to 30s, and up to 50 references (30 images, 10 videos, 10 audios) to "
        "hold a subject across it; audio generated jointly with the picture for tighter lip-sync; "
        "start+end frame. Pricier per second than 2.0",
        # PARITY: WaveSpeed serves several extra 2.5 endpoints (turbo tiers, video-edit,
        # video-extend) that fal does not. An alias needs both lanes, so none of them is carried.
        _ws_seedance("bytedance/seedance-2.5",
                     "$0.36/s at 720p ($0.18 480p, $0.90 1080p, $1.80 4k); with reference videos "
                     "$0.22/s at 720p billed across reference + output seconds",
                     durations=_SD25_DURATIONS, max_refs=_SD25_REFS, i2v_aspect=False),
        # fal bills 2.5 by token — ~$0.0214/1K, tokens = h*w*seconds*24/1024 — and caps at 720p.
        _seedance("bytedance/seedance-2.5", ["480p", "720p"],
                  price="~$0.47/s at 720p, ~$0.22/s at 480p; references billed at 0.6x",
                  durations=_SD25_DURATIONS, max_refs=_SD25_REFS, i2v_aspect=False)),
    "seedance-2.0": _one("Seedance 2.0 (ByteDance)",
        "cinematic default workhorse; native synced audio, real-world physics and camera control; "
        "start+end frame and image/video/audio references",
        _ws_seedance("bytedance/seedance-2.0", "$0.24/s at 720p ($0.12 480p, $0.60 1080p, $1.20 4k)"),
        _seedance("bytedance/seedance-2.0", ["480p", "720p", "1080p", "4k"],
                  price="~$0.30/s at 720p")),
    "seedance-2.0-fast": _one("Seedance 2.0 Fast (ByteDance)",
        "speed-optimised Seedance 2.0 at ~33% lower cost, same native audio and reference support; "
        "the draft tier when you'll re-run the winner on the standard model",
        _ws_seedance("bytedance/seedance-2.0-fast", "$0.20/s at 720p ($0.10 480p, $0.50 1080p, $1.00 4k)"),
        _seedance("bytedance/seedance-2.0/fast", ["480p", "720p", "1080p", "4k"],
                  price="see fal.ai/models")),
    "seedance-2.0-mini": _one("Seedance 2.0 Mini (ByteDance)",
        "faster, lower-cost Seedance with native audio",
        _ws_seedance("bytedance/seedance-2.0-mini", "$0.12/s at 720p ($0.06 480p, $0.30 1080p, $0.60 4k)"),
        _seedance("bytedance/seedance-2.0/mini", ["480p", "720p"], price="see fal.ai/models")),
    "kling-3.0-pro": _one("Kling 3.0 Pro (Kuaishou)",
        "top-tier image-to-video, fluid cinematic motion, native audio; start and start+end frame",
        _ws_kling("kwaivgi/kling-v3.0-pro", "$0.112/s silent, $0.168/s with audio"),
        _kling("fal-ai/kling-video/v3/pro", list(range(3, 16)), price="see fal.ai/models")),
    "kling-3.0-standard": _one("Kling 3.0 Standard (Kuaishou)",
        "standard-tier Kling 3.0; native audio; start and start+end frame",
        _ws_kling("kwaivgi/kling-v3.0-std", "$0.084/s silent, $0.126/s with audio"),
        _kling("fal-ai/kling-video/v3/standard", list(range(3, 16)), price="see fal.ai/models")),
    "veo-3.1": _one("Veo 3.1 (Google)",
        "premium cinematic motion, strong prompt adherence, native audio with dialogue and lip-sync; "
        "start frame, start+end frame, and image references",
        _ws_veo("google/veo3.1", ["720p", "1080p", "4k"], "$0.40/s with audio, $0.20/s silent"),
        _veo("fal-ai/veo3.1", ["720p", "1080p", "4k"],
             price="$0.20/s (+$0.20/s with audio); 4k $0.40/s")),
    "veo-3.1-fast": _one("Veo 3.1 Fast (Google)",
        "faster, cheaper Veo 3.1 with native audio; start / start+end frame and image references",
        _ws_veo("google/veo3.1-fast", ["720p", "1080p"], "$0.15/s with audio, $0.10/s silent"),
        _veo("fal-ai/veo3.1/fast", ["720p", "1080p", "4k"], price="see fal.ai/models")),
    "veo-3.1-lite": _one("Veo 3.1 Lite (Google)",
        "lightweight Veo 3.1 tier for quick drafts; start frame and start+end frame (silent, no references)",
        # Lite is its own shape, not a _ws_veo tier: no audio toggle anywhere, no reference-to-video
        # endpoint at all, no `last_image` on image-to-video — start+end is a distinct endpoint.
        _ws_vroute("$0.30 per 6s at 720p, $0.48 at 1080p; start+end $0.40 / $0.64",
            t2v=_ws_ep("google/veo3.1-lite/text-to-video", aspects=VIDEO_ASPECTS,
                       durations=[4, 6, 8], resolutions=["720p", "1080p"]),
            i2v=_ws_ep("google/veo3.1-lite/image-to-video",
                       media={"start_frame_image": "image"}, media_scalar=("image",),
                       aspects=VIDEO_ASPECTS, durations=[4, 6, 8], resolutions=["720p", "1080p"],
                       requires=("start_frame_image",)),
            flf=_ws_ep("google/veo3.1-lite/start-end-to-video", media=_WS_FRAMES,
                       media_scalar=_WS_FRAME_SCALAR, aspects=VIDEO_ASPECTS,
                       resolutions=["720p", "1080p"],       # no duration control on this endpoint
                       requires=("start_frame_image", "end_frame_image"))),
        _veo("fal-ai/veo3.1/lite", ["720p", "1080p"], price="see fal.ai/models", references=False)),
    "grok-imagine-video": _one("Grok Imagine Video (xAI)",
        "fast, permissive text/image-to-video drafts with native audio; image references and video-to-video edit",
        _ws_vroute("$0.30 per 6s, $0.50 per 10s; edit $0.065/s",
            max_refs={"reference_images": 7, "reference_videos": 1},
            t2v=_ws_ep("x-ai/grok-imagine-video/text-to-video", aspects=VIDEO_ASPECTS,
                       durations=[6, 10], resolutions=["480p", "720p"]),
            i2v=_ws_ep("x-ai/grok-imagine-video/image-to-video",
                       media={"start_frame_image": "image"}, media_scalar=("image",),
                       durations=[6, 10], resolutions=["480p", "720p"],
                       requires=("start_frame_image",)),
            r2v=_ws_ep("x-ai/grok-imagine-video/reference-to-video",
                       media={"reference_images": "images"}, durations=[6, 10],
                       resolutions=["480p", "720p"]),
            v2v=_ws_ep("x-ai/grok-imagine-video/edit-video",   # Grok's only video input is edit
                       media={"reference_videos": "video"}, media_scalar=("video",),
                       resolutions=["480p", "720p"])),
        _vroute(max_refs={"reference_images": 7, "reference_videos": 1}, price="~$4.20/min incl. audio",
            t2v=_ep("xai/grok-imagine-video/text-to-video", aspects=VIDEO_ASPECTS,
                    durations=list(range(1, 16)), resolutions=["480p", "720p"]),
            i2v=_ep("xai/grok-imagine-video/image-to-video", media={"start_frame_image": "image_url"},
                    aspects=VIDEO_ASPECTS, durations=list(range(1, 16)), resolutions=["480p", "720p"]),
            r2v=_ep("xai/grok-imagine-video/reference-to-video",
                    media={"reference_images": "reference_image_urls"}, aspects=VIDEO_ASPECTS,
                    durations=list(range(1, 16)), resolutions=["480p", "720p"]),
            v2v=_ep("xai/grok-imagine-video/edit-video",
                    media={"reference_videos": "video_url"}, resolutions=["480p", "720p"]))),
    "gemini-omni": _one("Gemini Omni Flash (Google)",
        "fast multimodal generation with strong coherence and character consistency; native audio; "
        "start frame and image references (fixed 720p, no end frame)",
        _ws_vroute("$1.04 per 8s (t2v), $1.12 (i2v), $1.28 (references)",
            max_refs={"reference_images": 7},   # Google: up to 7 reference images
            t2v=_ws_ep("google/gemini-omni-flash/text-to-video", aspects=VIDEO_ASPECTS,
                       durations=list(range(3, 11))),
            i2v=_ws_ep("google/gemini-omni-flash/image-to-video",
                       media={"start_frame_image": "image"}, media_scalar=("image",),
                       aspects=VIDEO_ASPECTS, durations=list(range(3, 11)),
                       requires=("start_frame_image",)),
            r2v=_ws_ep("google/gemini-omni-flash/reference-to-video",
                       media={"reference_images": "images"}, aspects=VIDEO_ASPECTS,
                       durations=list(range(3, 11)))),
        _vroute(max_refs={"reference_images": 7}, price="see fal.ai/models",
            t2v=_ep("google/gemini-omni-flash", aspects=VIDEO_ASPECTS, durations=list(range(3, 11))),
            i2v=_ep("google/gemini-omni-flash/image-to-video", media={"start_frame_image": "image_url"},
                    aspects=VIDEO_ASPECTS, durations=list(range(3, 11))),
            r2v=_ep("google/gemini-omni-flash/reference-to-video",
                    media={"reference_images": "image_urls"}, aspects=VIDEO_ASPECTS,
                    durations=list(range(3, 11))))),
    "wan-2.7": _one("Wan 2.7 (Alibaba)",
        "smooth motion and scene fidelity; start+end frame, driving audio, and image/video references",
        # Wan takes a driving audio TRACK rather than an audio on/off toggle, hence audio_param=None.
        _ws_vroute("$0.50 per 5s at 720p, $0.75 at 1080p; references $1.00 / $1.60",
            combined_ref_max=5,
            max_refs={"reference_images": 5, "reference_videos": 5, "reference_audios": 1},
            t2v=_ws_ep("alibaba/wan-2.7/text-to-video",
                       media={"reference_audios": "audio"}, media_scalar=("audio",),
                       aspects=VIDEO_ASPECTS, durations=list(range(2, 16)),
                       resolutions=["720p", "1080p"]),
            i2v=_ws_ep("alibaba/wan-2.7/image-to-video",
                       media={**_WS_FRAMES, "reference_audios": "audio"},
                       media_scalar=(*_WS_FRAME_SCALAR, "audio"),
                       durations=list(range(2, 16)), resolutions=["720p", "1080p"],
                       requires=("start_frame_image",)),
            r2v=_ws_ep("alibaba/wan-2.7/reference-to-video",
                       media={"reference_images": "reference_images", "reference_videos": "videos"},
                       aspects=VIDEO_ASPECTS, durations=list(range(2, 11)),
                       resolutions=["720p", "1080p"])),
        # fal: up to 5 references (images + videos combined); driving audio is a single track.
        _vroute(combined_ref_max=5, price="see fal.ai/models",
            max_refs={"reference_images": 5, "reference_videos": 5, "reference_audios": 1},
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
AUDIO_TYPES = ["speech", "music", "sfx"]

# Default clip length (seconds) for the non-speech modes when the caller omits `duration` — billing
# is per-second, so this must be concrete (never guessed at request time).
AUDIO_DEFAULT_DURATION = {"music": 30, "sfx": 5}

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
    # --- non-speech modes (C7). Music is queue-based → `queued: True` routes it through the async
    # lane (the async consumer reads this flag, and the skills provider exposes audio_submit/audio_status); SFX is
    # fast and synchronous. Vendor endpoint ids are tunable constants — verify at the BYOK smoke. ---
    "stable-audio": {
        "display": "Music generation",
        "strengths": "instrumental music beds and background tracks from a text prompt",
        "price": "metered per second of audio",
        "types": ["music"],
        "queued": True,
        "routes": [_route("fal", "fal-ai/stable-audio",
                          supports={"prompt", "duration"})],   # format not wired on the fal music route
    },
    "eleven-sfx": {
        "display": "Sound Effects generation",
        "strengths": "short sound effects, ambience and foley from a text prompt",
        "price": "metered per second of audio",
        "types": ["sfx"],
        "routes": [_route("elevenlabs", "eleven_sfx",
                          supports={"prompt", "duration", "format"})],
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


# --- research: read-only public data from social platforms + ad libraries -------------------
# One generic call shape (platform + endpoint + params). Each entry carries the vendor path (the
# ALLOW-LIST — a caller never supplies a URL, the path is chosen by the platform/endpoint enum),
# the params contract, a per-call credit cost, and a capability-shaped description (never
# vendor-shaped, so another research vendor could back the same entries with no agent-contract
# change). `cost_credits` is the endpoint's per-call credit cost. Every endpoint here is a GET read.
RESEARCH_SOURCES = {
    "meta_ad_library": {
        "search_companies": {"path": "/v1/facebook/adLibrary/search/companies",
            "required": ["query"], "optional": [], "cost_credits": 1,
            "desc": "Find advertisers on Meta's Ad Library by name — returns each company's page id."},
        "company_ads": {"path": "/v1/facebook/adLibrary/company/ads", "required": [],
            "optional": ["companyName", "pageId", "country", "status", "media_type", "language",
                         "sort_by", "start_date", "end_date", "cursor", "trim"], "cost_credits": 1,
            "desc": "A competitor's active Meta ads (Facebook/Instagram) — pass companyName, or a "
                    "pageId from search_companies. Filter by country, status, media_type, date range."},
        "search_ads": {"path": "/v1/facebook/adLibrary/search/ads", "required": ["query"],
            "optional": ["country", "status", "media_type", "cursor", "trim"], "cost_credits": 1,
            "desc": "Search Meta Ad Library ads by keyword across advertisers."},
    },
    "linkedin_ads": {
        "search": {"path": "/v1/linkedin/ads/search", "required": [],
            "optional": ["company", "keyword", "companyId", "countries", "startDate", "endDate",
                         "paginationToken"], "cost_credits": 1,
            "desc": "Search LinkedIn ads — pass company, keyword, or companyId (+ optional countries, "
                    "date range). Returns advertisers' ad creatives."},
        "ad": {"path": "/v1/linkedin/ad", "required": ["url"], "optional": [], "cost_credits": 1,
            "desc": "A single LinkedIn ad's details by URL."},
    },
    "instagram": {
        "profile": {"path": "/v1/instagram/profile", "required": ["handle"], "optional": [],
            "cost_credits": 1, "desc": "A public Instagram profile — bio, follower/following counts, verification."},
        "posts": {"path": "/v1/instagram/user/reels", "required": ["handle"], "optional": ["max_id"],
            "cost_credits": 1, "desc": "Recent reels/posts from an Instagram account (paginate with max_id)."},
        "post": {"path": "/v1/instagram/post", "required": ["url"], "optional": [], "cost_credits": 1,
            "desc": "A single Instagram post/reel by URL — caption, media, engagement."},
        "transcript": {"path": "/v2/instagram/media/transcript", "required": ["url"], "optional": [],
            "cost_credits": 1, "desc": "Spoken-word transcript of an Instagram reel/video."},
    },
    "tiktok": {
        "profile": {"path": "/v1/tiktok/profile", "required": ["handle"], "optional": [],
            "cost_credits": 1, "desc": "A public TikTok profile — bio, follower counts, verification."},
        "posts": {"path": "/v3/tiktok/profile/videos", "required": ["handle"],
            "optional": ["max_cursor", "sort_by"], "cost_credits": 1,
            "desc": "Recent videos from a TikTok account (sort_by latest/popular; paginate with max_cursor)."},
        "comments": {"path": "/v1/tiktok/video/comments", "required": ["url"], "optional": ["cursor"],
            "cost_credits": 1, "desc": "Comments on a TikTok video by URL (audience listening)."},
        "hashtag": {"path": "/v1/tiktok/search/hashtag", "required": ["hashtag"], "optional": ["cursor"],
            "cost_credits": 1, "desc": "Videos for a TikTok hashtag (trend/topic discovery)."},
        "search": {"path": "/v1/tiktok/search/keyword", "required": ["query"], "optional": ["cursor"],
            "cost_credits": 1, "desc": "TikTok keyword video search (content / trend discovery)."},
        "search_users": {"path": "/v1/tiktok/search/users", "required": ["query"], "optional": ["cursor"],
            "cost_credits": 1, "desc": "Find TikTok creators by keyword."},
        "trending": {"path": "/v1/tiktok/get-trending-feed", "required": ["region"], "optional": [],
            "cost_credits": 1, "desc": "TikTok trending feed for a region (a 2-letter code, e.g. US)."},
        "video": {"path": "/v2/tiktok/video", "required": ["url"], "optional": [], "cost_credits": 1,
            "desc": "A single TikTok video by URL — caption, stats, author."},
        "transcript": {"path": "/v1/tiktok/video/transcript", "required": ["url"], "optional": [],
            "cost_credits": 1, "desc": "Spoken-word transcript of a TikTok video."},
    },
    "youtube": {
        "search": {"path": "/v1/youtube/search", "required": ["query"], "optional": [], "cost_credits": 1,
            "desc": "YouTube search results for a query — videos and channels."},
        "channel": {"path": "/v1/youtube/channel", "required": ["handle"], "optional": [], "cost_credits": 1,
            "desc": "A YouTube channel's public details and stats (pass an @handle)."},
        "video": {"path": "/v1/youtube/video", "required": ["url"], "optional": [], "cost_credits": 1,
            "desc": "A single YouTube video/short by URL — title, stats, metadata."},
        "transcript": {"path": "/v1/youtube/video/transcript", "required": ["url"], "optional": [],
            "cost_credits": 1, "desc": "Transcript of a YouTube video by URL."},
    },
    "reddit": {
        "search": {"path": "/v1/reddit/search", "required": ["query"], "optional": ["sort", "after"],
            "cost_credits": 1, "desc": "Reddit post search across subreddits for a keyword (audience listening)."},
        "subreddit": {"path": "/v1/reddit/subreddit", "required": ["subreddit"], "optional": ["sort", "after"],
            "cost_credits": 1, "desc": "Recent posts in a subreddit."},
        "subreddit_details": {"path": "/v1/reddit/subreddit/details", "required": ["subreddit"],
            "optional": [], "cost_credits": 1,
            "desc": "A subreddit's about data — subscriber count, description, rules."},
        "subreddit_search": {"path": "/v1/reddit/subreddit/search", "required": ["query"], "optional": [],
            "cost_credits": 1, "desc": "Find subreddits by keyword."},
        "comments": {"path": "/v1/reddit/post/comments", "required": ["url"], "optional": [],
            "cost_credits": 1, "desc": "Comments on a Reddit post by URL (audience listening)."},
        "transcript": {"path": "/v1/reddit/post/transcript", "required": ["url"], "optional": [],
            "cost_credits": 1, "desc": "Transcript of a Reddit post's media by URL."},
    },
    "x": {
        "profile": {"path": "/v1/twitter/profile", "required": ["handle"], "optional": [], "cost_credits": 1,
            "desc": "A public X/Twitter profile — bio, follower/following counts, verification."},
        "posts": {"path": "/v1/twitter/user-tweets", "required": ["handle"], "optional": [],
            "cost_credits": 1, "desc": "Recent posts from an X/Twitter account."},
        "post": {"path": "/v1/twitter/tweet", "required": ["url"], "optional": [], "cost_credits": 1,
            "desc": "A single X/Twitter post by URL — text, author, engagement."},
        "transcript": {"path": "/v1/twitter/tweet/transcript", "required": ["url"], "optional": [],
            "cost_credits": 1, "desc": "Transcript of an X/Twitter post's video by URL."},
    },
    "linkedin": {
        "profile": {"path": "/v1/linkedin/profile", "required": ["url"], "optional": [], "cost_credits": 1,
            "desc": "A public LinkedIn person profile by URL."},
        "company": {"path": "/v1/linkedin/company", "required": ["url"], "optional": [], "cost_credits": 1,
            "desc": "A LinkedIn company page by URL."},
        "post": {"path": "/v1/linkedin/post", "required": ["url"], "optional": [], "cost_credits": 1,
            "desc": "A single LinkedIn post by URL."},
    },
    "threads": {
        "profile": {"path": "/v1/threads/profile", "required": ["handle"], "optional": [], "cost_credits": 1,
            "desc": "A public Threads profile — bio, follower counts."},
        "posts": {"path": "/v1/threads/user/posts", "required": ["handle"], "optional": [],
            "cost_credits": 1, "desc": "Recent posts from a Threads account."},
        "post": {"path": "/v1/threads/post", "required": ["url"], "optional": [], "cost_credits": 1,
            "desc": "A single Threads post by URL."},
        "search": {"path": "/v1/threads/search", "required": ["query"], "optional": [],
            "cost_credits": 1, "desc": "Threads keyword search (audience listening / trend discovery)."},
        "search_users": {"path": "/v1/threads/search/users", "required": ["query"], "optional": [],
            "cost_credits": 1, "desc": "Find Threads users by keyword."},
    },
    "pinterest": {
        "search": {"path": "/v1/pinterest/search", "required": ["query"], "optional": ["cursor"],
            "cost_credits": 1, "desc": "Pinterest pin search for a keyword (visual / product discovery)."},
        "pin": {"path": "/v1/pinterest/pin", "required": ["url"], "optional": [], "cost_credits": 1,
            "desc": "A single Pinterest pin by URL — image, description, destination link."},
        "boards": {"path": "/v1/pinterest/user/boards", "required": ["handle"], "optional": [],
            "cost_credits": 1, "desc": "A Pinterest user's public boards."},
        "board": {"path": "/v1/pinterest/board", "required": ["url"], "optional": ["cursor"],
            "cost_credits": 1, "desc": "A Pinterest board's pins by URL."},
    },
    "bluesky": {
        "profile": {"path": "/v1/bluesky/profile", "required": ["handle"], "optional": [], "cost_credits": 1,
            "desc": "A public Bluesky profile."},
        "posts": {"path": "/v1/bluesky/user/posts", "required": ["handle"], "optional": ["cursor"],
            "cost_credits": 1, "desc": "Recent posts from a Bluesky account."},
        "post": {"path": "/v1/bluesky/post", "required": ["url"], "optional": [], "cost_credits": 1,
            "desc": "A single Bluesky post by URL."},
    },
}

# One routing alias — the (platform, endpoint) choice + params ride as the tool's input, so the
# whole endpoint surface is one route. A second research vendor later = one more route here.
RESEARCH_MODELS = {
    "social-research": {
        "display": "Social & Ad-Library Research",
        "strengths": "structured public data from social platforms and ad libraries — competitor "
        "ads, profiles, posts, comments, search",
        "price": "metered per call; call list_research_sources for the per-endpoint cost",
        "routes": [_route("scrapecreators", "scrapecreators-v1",
                          supports={"platform", "endpoint", "params"})],
    },
}

# Speech-to-text with word timestamps. One route today (Scribe); a second STT vendor later = one
# more route here — the tool contract (audio in, {text, words} out) is vendor-agnostic.
TRANSCRIBE_MODELS = {
    "scribe": {
        "display": "Scribe (speech-to-text with word timestamps)",
        "strengths": "accurate transcription with word-level timestamps for captions and "
        "competitor-ad audio analysis; 90+ languages",
        "price": "metered per minute of audio",
        "routes": [_route("elevenlabs", "scribe_v1", supports={"audio", "language"})],
    },
}


def research_source(platform, endpoint):
    """The curated entry for (platform, endpoint), or None. The vendor path lives here — it is
    chosen by this enum, never supplied by the caller (the catalog is the request allow-list)."""
    return (RESEARCH_SOURCES.get((platform or "").strip().lower()) or {}).get(
        (endpoint or "").strip().lower())


def research_validate(platform, endpoint, params):
    """Validate a research request against the catalog — returns None if OK, else a reason string.
    Checks the source exists, `params` is an object, every required param is present, and no unknown
    param is passed. One shared validator so every caller rejects the same bad requests up front,
    before a call is made."""
    entry = research_source(platform, endpoint)
    if entry is None:
        return f"unknown research source: {platform or '?'}/{endpoint or '?'}"
    if params is not None and not isinstance(params, dict):
        return "params must be an object of query parameters."
    params = params or {}
    required = list(entry.get("required", []))
    missing = [p for p in required if not str(params.get(p, "")).strip()]
    if missing:
        return f"{platform}/{endpoint} is missing required params: {', '.join(missing)}"
    allowed = set(required) | set(entry.get("optional", []))
    unknown = [k for k in params if k not in allowed]
    if unknown:
        return f"{platform}/{endpoint} got unknown params: {', '.join(unknown)}"
    return None


def research_sources_listing(query=None):
    """Discovery payload for list_research_sources: every platform's endpoints with their params
    contract and per-call cost. `query` filters by platform/endpoint/description keyword."""
    q = (query or "").lower().strip()
    platforms = {}
    for platform, endpoints in RESEARCH_SOURCES.items():
        rows = []
        for ep, e in endpoints.items():
            if q and q not in f"{platform} {ep} {e.get('desc', '')}".lower():
                continue
            rows.append({"endpoint": ep, "description": e.get("desc", ""),
                         "required_params": list(e.get("required", [])),
                         "optional_params": list(e.get("optional", [])),
                         "cost_credits": e.get("cost_credits")})
        if rows:
            platforms[platform] = rows
    return {"ok": True, "platforms": platforms,
            "usage": "call social_research with platform, endpoint, and a params object built from "
                     "the required/optional params above."}


# capability -> model table. Adding a capability = one entry here + a table above.
_TABLES = {"image": IMAGE_MODELS, "video": VIDEO_MODELS, "audio": AUDIO_MODELS,
           "extract": EXTRACT_MODELS, "analysis": ANALYSIS_MODELS, "research": RESEARCH_MODELS,
           "transcribe": TRANSCRIBE_MODELS}
DEFAULTS = {"image": DEFAULT_MODEL, "video": "seedance-2.0-fast", "audio": "eleven-v3",
            "extract": "web-extract", "analysis": "gemini-flash-latest", "research": "social-research",
            "transcribe": "scribe"}


def get(capability, model):
    """Catalog entry for (capability, model), or None."""
    return (_TABLES.get(capability) or {}).get(model)


def routes_of(capability, model):
    """Ordered provider routes for (capability, model) (priority order); [] if unknown."""
    return ((_TABLES.get(capability) or {}).get(model) or {}).get("routes", [])


def serving_route(capability, model):
    """The route that would actually serve this alias for THIS caller, so discovery quotes the lane
    they're on. Falls back to the first route when nothing resolves — on the managed lane that is
    also the vendor the server generates on, so the quote stays honest. The client import is
    deferred: client imports us at module load, so a top-level one would cycle."""
    routes = routes_of(capability, model)
    if not routes:
        return None
    from . import client                                        # noqa: PLC0415 — deferred, see above
    kind, _provider, route = client.select_route(capability, model)
    return route if kind == "direct" and route else routes[0]


def price_of(capability, model, meta=None):
    """The price string to show for an alias: the serving route's own, since the lanes bill
    differently. Capabilities with a single provider (audio/analysis/extract) keep theirs on the
    alias, so that wins when present."""
    meta = meta if meta is not None else (get(capability, model) or {})
    if meta.get("price"):
        return meta["price"]
    route = serving_route(capability, model)
    return (route or {}).get("price") or "see the provider's model page"


def default_model(capability):
    """The default alias for a capability (used when the agent omits `model`)."""
    return DEFAULTS.get(capability)


def default_audio_model(audio_type):
    """The default audio model for a `type` — speech uses the capability default; music/sfx use the
    first model that advertises that type."""
    if audio_type == "speech":
        return DEFAULTS.get("audio")
    for name, entry in AUDIO_MODELS.items():
        if audio_type in entry.get("types", []):
            return name
    return DEFAULTS.get("audio")


def image_aspects(route):
    """The aspect ratios this image route accepts (its `sizes` map is the authority)."""
    return list(route["sizes"])


def image_resolutions(route):
    """The resolution tiers this image route renders at, from the tiers the tool exposes.

    Empty means the model has no resolution control at all — it renders at its own native tier, and
    a request for a higher one has to be refused rather than quietly downgraded. A route that takes
    `resolution` but declares no allow-list accepts every exposed tier."""
    if "resolution" not in (route.get("supports") or ()):
        return []
    allowed = route.get("resolutions")
    if not allowed:
        return list(IMAGE_RESOLUTIONS)
    return [r for r in IMAGE_RESOLUTIONS if r in allowed]


def image_models_listing(query=None):
    """Discovery payload for list_image_models: default model + the valid aspect ratios and
    resolution tiers image_generate accepts + the models (optionally filtered by `query`).
    `aspect_ratios` at the top level is the union; each model carries the set it actually
    accepts, because they differ."""
    models = list_models("image", query)
    for row in models:
        route = serving_route("image", row["model"])
        if route:
            row["aspect_ratios"] = image_aspects(route)
            # The tiers this model actually renders at. Empty list = no resolution control; it has
            # one native tier and `resolution` is refused rather than silently dropped.
            row["resolutions"] = image_resolutions(route)
            # How many reference images this model takes on the lane that will serve it. The two
            # lanes' ceilings differ (WaveSpeed's grok edit takes one; fal's takes three), and a cap
            # is a quantity rather than a missing capability — so it's reported, not levelled down.
            row["max_reference_images"] = route["max_refs"]
    return {"ok": True, "default": DEFAULT_MODEL, "aspect_ratios": IMAGE_ASPECTS,
            "resolutions": IMAGE_RESOLUTIONS, "models": models}


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
    combination — e.g. a start frame together with references (they live on different endpoints).

    Endpoints whose own `requires` aren't met sort LAST rather than being excluded. Two reasons:
    on WaveSpeed, Seedance's references live on text-to-video while image-to-video (which demands a
    start frame) declares fewer media keys, so plain fewest-keys would hand a bare text prompt to
    image-to-video; and keeping an unmet endpoint as a last resort is what lets the caller answer
    "this mode needs a start frame" instead of the vaguer "no endpoint takes that combination"."""
    covering = [ep for ep in route["endpoints"].values() if set(populated) <= set(ep["media"])]
    return min(covering, key=lambda ep: (not set(ep.get("requires", ())) <= set(populated),
                                         len(ep["media"]))) if covering else None


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
            "price": price_of("video", name, meta), "modes": sorted(route["endpoints"].keys()),
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
        models.append(_video_model_detail(name, meta, serving_route("video", name)))
    return {"ok": True, "default": DEFAULTS["video"], "aspect_ratios": VIDEO_ASPECTS,
            "resolutions": VIDEO_RESOLUTIONS, "models": models}


def list_models(capability, query=None):
    """Agent-facing discovery for a capability: name/display/strengths/price (+types for audio)."""
    q = (query or "").lower().strip()
    out = []
    for name, m in (_TABLES.get(capability) or {}).items():
        if q and q not in f"{name} {m['display']} {m['strengths']}".lower():
            continue
        row = {"model": name, "display": m["display"], "strengths": m["strengths"],
               "price": price_of(capability, name, m)}
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
    # ---- both lanes present on every image/video alias, wavespeed first ----
    for _cap, _table in (("image", IMAGE_MODELS), ("video", VIDEO_MODELS)):
        for _m in _table:
            _rs = routes_of(_cap, _m)
            assert [r["provider"] for r in _rs] == ["wavespeed", "fal"], (_cap, _m, _rs)
            assert all(r.get("price") for r in _rs), f"{_cap}/{_m} route missing a price"
    assert default_model("video") == "seedance-2.0-fast"
    assert len(VIDEO_MODELS) == 12 and len(IMAGE_MODELS) == 8

    # ---- fal endpoint resolution is unchanged ----
    _sd = routes_of("video", "seedance-2.0")[1]
    assert _sd["provider"] == "fal"
    assert video_endpoint_for(_sd, set())["id"].endswith("text-to-video")
    assert video_endpoint_for(_sd, {"start_frame_image"})["id"].endswith("image-to-video")
    assert video_endpoint_for(_sd, {"reference_audios"})["id"].endswith("reference-to-video")
    _veo = routes_of("video", "veo-3.1")[1]
    assert video_endpoint_for(_veo, {"start_frame_image"})["id"].endswith("image-to-video")
    assert video_endpoint_for(_veo, {"start_frame_image", "end_frame_image"})["id"].endswith("first-last-frame-to-video")
    assert video_endpoint_for(routes_of("video", "grok-imagine-video")[1], {"start_frame_image", "reference_images"}) is None
    assert "reference_videos" not in video_media_kinds(_veo)   # veo has no video references

    # ---- parity: the two lanes advertise the SAME media surface for every alias ----
    for _m in VIDEO_MODELS:
        _w, _f = routes_of("video", _m)
        assert video_media_kinds(_w) == video_media_kinds(_f), (
            _m, sorted(video_media_kinds(_w)), sorted(video_media_kinds(_f)))
        assert _w["max_refs"] == _f["max_refs"], (_m, _w["max_refs"], _f["max_refs"])
    # Kling is frames-only on both — wavespeed can't do URL references, so fal doesn't offer them
    for _m in ("kling-3.0-pro", "kling-3.0-standard"):
        for _r in routes_of("video", _m):
            assert video_media_kinds(_r) == {"start_frame_image", "end_frame_image"}, (_m, _r["provider"])
            assert not _r["max_refs"] and _r.get("combined_ref_max") is None, (_m, _r["provider"])
    # veo lite has no reference mode on either lane (wavespeed serves none)
    for _r in routes_of("video", "veo-3.1-lite"):
        assert "r2v" not in _r["endpoints"] and "reference_images" not in video_media_kinds(_r), _r["provider"]
    assert _video_model_detail("veo-3.1", VIDEO_MODELS["veo-3.1"], _veo)["media"]["end_frame_image"] is True

    # ---- wavespeed endpoint resolution: fewer endpoints, same reach ----
    _wsd = routes_of("video", "seedance-2.0")[0]
    # references live on text-to-video here, and a bare prompt must NOT fall into image-to-video
    # even though that endpoint declares fewer media keys — `requires` breaks the tie.
    assert video_endpoint_for(_wsd, set())["id"].endswith("text-to-video")
    assert video_endpoint_for(_wsd, {"reference_audios"})["id"].endswith("text-to-video")
    assert video_endpoint_for(_wsd, {"start_frame_image"})["id"].endswith("image-to-video")
    assert video_endpoint_for(_wsd, {"start_frame_image", "end_frame_image"})["id"].endswith("image-to-video")
    _wveo = routes_of("video", "veo-3.1")[0]
    # start+end folds into image-to-video on this lane (no separate first-last-frame endpoint)
    assert video_endpoint_for(_wveo, {"start_frame_image", "end_frame_image"})["id"].endswith("image-to-video")
    assert video_endpoint_for(_wveo, {"reference_images"})["id"].endswith("reference-to-video")
    # veo lite keeps a distinct start-end endpoint, because its image-to-video has no last_image
    _wlite = routes_of("video", "veo-3.1-lite")[0]
    assert video_endpoint_for(_wlite, {"start_frame_image"})["id"].endswith("image-to-video")
    assert video_endpoint_for(_wlite, {"start_frame_image", "end_frame_image"})["id"].endswith("start-end-to-video")
    assert video_endpoint_for(_wlite, {"reference_images"}) is None      # lite has no references
    # Wan's driving audio is a single track that rides along with a start frame
    _wwan = routes_of("video", "wan-2.7")[0]
    assert video_endpoint_for(_wwan, set())["id"].endswith("text-to-video")
    assert video_endpoint_for(_wwan, {"reference_audios"})["id"].endswith("text-to-video")
    assert video_endpoint_for(_wwan, {"start_frame_image", "reference_audios"})["id"].endswith("image-to-video")
    # Kling carries no references on either lane (parity: wavespeed can't serve them)
    _wkl = routes_of("video", "kling-3.0-pro")[0]
    assert video_media_kinds(_wkl) == {"start_frame_image", "end_frame_image"}, video_media_kinds(_wkl)
    assert _wkl["audio_param"] == "sound"        # Kling's toggle is not generate_audio

    # ---- seedance 2.5: 30s ceiling, 50 references, no aspect control on image-to-video ----
    _w25, _f25 = routes_of("video", "seedance-2.5")
    for _r in (_w25, _f25):
        _e = _r["endpoints"]
        assert _e["t2v"]["durations"] == list(range(4, 31)), (_r["provider"], _e["t2v"]["durations"])
        # output ratio follows the input frame here, so the ratio is not sent (fal takes only "auto")
        assert not _e["i2v"]["aspects"] and _e["t2v"]["aspects"] == VIDEO_ASPECTS, _r["provider"]
        assert _r["max_refs"] == {"reference_images": 30, "reference_videos": 10,
                                  "reference_audios": 10}, _r["provider"]
    assert _f25["endpoints"]["t2v"]["resolutions"] == ["480p", "720p"]   # fal serves no 1080p/4k tier
    assert _w25["endpoints"]["t2v"]["resolutions"] == VIDEO_RESOLUTIONS
    # same lane split as 2.0: references ride text-to-video on wavespeed, their own endpoint on fal
    assert video_endpoint_for(_f25, {"reference_videos"})["id"].endswith("reference-to-video")
    assert video_endpoint_for(_w25, {"reference_videos"})["id"].endswith("text-to-video")
    assert video_endpoint_for(_w25, set())["id"].endswith("text-to-video")
    for _r in (_w25, _f25):
        assert video_endpoint_for(_r, {"start_frame_image", "end_frame_image"})["id"].endswith("image-to-video")
    # 2.0 keeps its own smaller ceilings — the shared builder must not have levelled them up
    assert routes_of("video", "seedance-2.0")[1]["endpoints"]["t2v"]["durations"] == list(range(4, 16))
    assert routes_of("video", "seedance-2.0")[0]["max_refs"]["reference_images"] == 9
    assert routes_of("video", "seedance-2.0-mini")[1]["endpoints"]["i2v"]["aspects"] == VIDEO_ASPECTS

    # ---- image routes: the edit endpoint's narrower surface, and FLUX's pixel sizes ----
    _wgrok = routes_of("image", "grok-imagine")[0]
    assert _wgrok["ref_scalar"] and _wgrok["ref_param"] == "image" and _wgrok["max_refs"] == 1
    assert "aspect_ratio" not in _wgrok["edit_supports"]      # grok's edit takes prompt + image only
    _wflux = routes_of("image", "flux-2-pro")[0]
    assert _wflux["size_style"] == "size_wh" and _wflux["sizes"]["16:9"] == "1344*768"
    assert "size" not in _wflux["edit_supports"]              # flux edit matches the input image
    assert set(_WS_SIZE) == set(IMAGE_ASPECTS)                # every exposed ratio has a pixel size
    assert routes_of("image", "seedream-5")[0]["resolutions"] == ["1k", "1.5k", "2k"]  # no 4k tier
    assert default_model("audio") == "eleven-v3"
    assert all(routes_of("audio", m) for m in AUDIO_MODELS)      # every audio model has a route
    assert routes_of("audio", "eleven-v3")[0]["provider"] == "elevenlabs"
    assert routes_of("audio", "eleven-v3")[0]["id"] == "eleven_v3"
    assert routes_of("audio", "stable-audio")[0]["provider"] == "fal"        # music via fal (queued)
    assert get("audio", "stable-audio").get("queued") is True
    assert routes_of("audio", "eleven-sfx")[0]["provider"] == "elevenlabs"   # sfx via elevenlabs
    assert default_audio_model("music") == "stable-audio" and default_audio_model("sfx") == "eleven-sfx"
    assert list_models("audio")[0]["types"] == ["speech"]
    # voices are account-level: never carried per model, only resolved live
    assert all("voices" not in m for m in list_models("audio"))
    _listing = audio_models_listing()
    assert _listing["default"] == "eleven-v3" and _listing["types"] == AUDIO_TYPES
    assert len(_listing["models"]) == 5      # 3 speech + music + sfx
    # voices moved to their own tool — the models payload must not carry them at all
    assert "voices" not in _listing and "list_voices" in _listing["voices_note"]
    assert list_models("audio", "long-form")[0]["model"] == "eleven-multilingual-v2"

    # ---- research: one alias -> scrapecreators; every source resolves + carries a cost ----
    assert routes_of("research", "social-research")[0]["provider"] == "scrapecreators"
    assert default_model("research") == "social-research"
    assert research_source("meta_ad_library", "company_ads")["path"].endswith("/company/ads")
    assert research_source("x", "PROFILE")["path"] == "/v1/twitter/profile"   # case-insensitive
    assert research_source("nope", "nope") is None
    for _plat, _eps in RESEARCH_SOURCES.items():
        for _ep, _e in _eps.items():
            assert _e.get("path", "").startswith("/v"), (_plat, _ep)
            assert isinstance(_e.get("cost_credits"), int) and _e["cost_credits"] > 0, (_plat, _ep)
            assert _e.get("desc"), (_plat, _ep)
    assert "meta_ad_library" in research_sources_listing()["platforms"]   # unfiltered lists all
    assert set(research_sources_listing("reddit")["platforms"]) == {"reddit"}   # query narrows
    print("catalog OK:", {c: list(t) for c, t in _TABLES.items()})
