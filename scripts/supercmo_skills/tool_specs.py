"""Shared media-tool schemas — one definition per tool, wrapped by the runtime."""
from . import catalog


def object_schema(properties, required):
    """Wrap shared properties as a JSON-Schema object body — the runtime supplies the outer key
    (`inputSchema` for MCP)."""
    return {"type": "object", "properties": properties, "required": required, "additionalProperties": False}


# ---------------------------------------------------------------------------- image_generate
IMAGE_GENERATE_DESCRIPTION = (
    "For a user's image request, load the `generating-images` skill BEFORE calling this — it picks "
    "the right model and builds the prompt (this tool does neither, and calling it raw gives weak, "
    "inconsistent results). "
    "Generate one or many still images from text prompts, optionally guided by reference "
    "images (a product photo, a character, a style or composition to follow). Pass `requests`: "
    "ONE object per image (wrap even a single image — `{ requests: [ { prompt } ] }`). Generate a "
    "batch of DIFFERENT images in a SINGLE call by adding more request objects (up to 10), each "
    "with its own prompt/model/aspect_ratio/resolution/reference_images; a single approval covers "
    "the whole batch. Each result carries a hosted image URL plus a local file `path`, or a "
    "structured error with a hint. Use for graphics, mockups, product/marketing visuals, logos, "
    "concept art, or to render a product or character from a supplied reference. "
    "Images are polled for you; a heavy image (large model / 4k / big batch) that runs long returns "
    "`{status:\"pending\", ...}` (a job handle, not an error) — pass that exact handle to `job_status` "
    "to retrieve it, and never re-submit a pending image. Set dry_run=true "
    "to preview the exact requests and cost without generating (no credits spent)."
)

IMAGE_GENERATE_PROPERTIES = {
    "requests": {
        "type": "array",
        "minItems": 1,
        "maxItems": 10,
        "description": "One object per image (wrap even a single image); add more objects to "
        "batch different images in one call (up to 10).",
        "items": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The image description. Be specific about subject, style, composition, and lighting.",
                },
                "model": {
                    "type": "string",
                    "default": catalog.DEFAULT_MODEL,
                    "description": f"Image model name. Omit to use the default ('{catalog.DEFAULT_MODEL}'). "
                    "If you need to choose and don't already have one in mind, call list_image_models.",
                },
                "aspect_ratio": {
                    "type": "string",
                    "enum": catalog.IMAGE_ASPECTS,
                    "default": catalog.IMAGE_DEFAULT_ASPECT,
                    "description": "Aspect ratio of the output image.",
                },
                "resolution": {
                    "type": "string",
                    "enum": catalog.IMAGE_RESOLUTIONS,
                    "default": catalog.IMAGE_DEFAULT_RESOLUTION,
                    "description": "Output resolution tier. Applied by models that support it; ignored by models that don't.",
                },
                "reference_images": {
                    "type": "array",
                    "items": {"type": "string"},
                    "maxItems": 10,
                    "description": "Optional reference image(s) — each a local file path or an "
                    "image URL. Use for product/character-driven generation or to follow a "
                    "supplied style or composition; if a model rejects the count, the error "
                    "states its limit. Omit for pure text-to-image.",
                },
            },
            "required": ["prompt"],
            "additionalProperties": False,
        },
    },
    "dry_run": {
        "type": "boolean",
        "description": "If true, return the requests that would be sent (keys masked), make no API call.",
        "default": False,
    },
}
IMAGE_GENERATE_REQUIRED = ["requests"]


# ---------------------------------------------------------------------------- list_image_models
LIST_IMAGE_MODELS_DESCRIPTION = (
    "List the available image-generation models (with strengths and price), plus the valid "
    "aspect ratios and resolution tiers that image_generate accepts. Use when you need to "
    "choose a model and don't already have one in mind (e.g. an open-ended request), or to "
    "check the valid aspect_ratio / resolution values — most of the time the model is the "
    "default or already specified. Pass an optional 'query' to filter models by use-case "
    "keyword (e.g. 'text', 'photorealistic', 'fast')."
)

LIST_IMAGE_MODELS_PROPERTIES = {
    "query": {
        "type": "string",
        "description": "Optional keyword to filter models by use-case (matches the name, display name, and strengths).",
    },
}
LIST_IMAGE_MODELS_REQUIRED = []


# ---------------------------------------------------------------------------- video_generate
VIDEO_GENERATE_DESCRIPTION = (
    "For a user's video request, load the `generating-videos` skill BEFORE calling this — it picks the "
    "right model and builds the motion prompt (this tool does neither, and calling it raw gives weak, "
    "generic clips). "
    "Generate one or many short video clips from text prompts, optionally guided by a start (and end) "
    "frame or by reference images, videos, or audio. Pass `requests`: ONE object per clip (wrap even a "
    "single clip — `{ requests: [ { prompt } ] }`); add more objects (up to 10) to batch DIFFERENT clips "
    "in one call, and repeat an object for variations of one prompt — a single approval covers the batch. "
    "Models differ in the aspect ratios, durations, resolutions, and media they accept — call "
    "list_video_models to check. "
    "Video generation is long-running: each clip is submitted and polled for you. A clip that "
    "finishes in time returns a hosted video URL plus a local file `path`; a clip still generating "
    "returns `{status:\"pending\", ...}` (a job handle, NOT an error) — pass that exact handle to "
    "`job_status` to retrieve it, and never re-submit a pending clip. Set dry_run=true to preview the "
    "exact requests without generating (no credits spent)."
)

_VIDEO_REF_ITEMS = {"type": "array", "items": {"type": "string"}}

VIDEO_GENERATE_PROPERTIES = {
    "requests": {
        "type": "array",
        "minItems": 1,
        "maxItems": 10,
        "description": "One object per clip (wrap even a single clip); add more objects to batch "
        "different clips in one call (up to 10).",
        "items": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string",
                    "description": "The video description. Be specific about subject, motion, camera "
                    "movement, pacing, and mood.",
                },
                "model": {
                    "type": "string",
                    "default": catalog.default_model("video"),
                    "description": f"Video model name. Omit to use the default "
                    f"('{catalog.default_model('video')}'). If you need to choose and don't already have "
                    "one in mind, call list_video_models.",
                },
                "start_frame_image": {
                    "type": "string",
                    "description": "Optional first frame to animate (image-to-video) — a local file path "
                    "or an image URL. Omit for pure text-to-video. Can't be combined with reference_* inputs.",
                },
                "end_frame_image": {
                    "type": "string",
                    "description": "Optional final frame — a local file path or an image URL — for a "
                    "start→end transition. Requires start_frame_image. Supported only by some models; the "
                    "error names them on a mismatch.",
                },
                "reference_images": {
                    **_VIDEO_REF_ITEMS,
                    "description": "Optional reference image(s) — local paths or URLs — guiding subject, "
                    "style, or composition (not frame-pinned). Support and max count vary by model "
                    "(list_video_models). Can't be combined with start/end frames.",
                },
                "reference_videos": {
                    **_VIDEO_REF_ITEMS,
                    "description": "Optional reference video(s) — local paths or URLs — for motion/style "
                    "transfer (video-to-video). Only some models accept them; see list_video_models.",
                },
                "reference_audios": {
                    **_VIDEO_REF_ITEMS,
                    "description": "Optional reference audio track(s) — local paths or URLs — the video is "
                    "generated to follow (e.g. lip-sync / timing). Only some models accept them.",
                },
                "duration": {
                    "type": "integer",
                    "description": "Clip length in seconds. Each model allows a different set; an "
                    "out-of-range value is snapped to the nearest valid one (see duration_adjusted in the result).",
                },
                "resolution": {
                    "type": "string",
                    "enum": catalog.VIDEO_RESOLUTIONS,
                    "description": "Output resolution tier. Applied by models that support it; the error "
                    "lists valid values on a mismatch.",
                },
                "aspect_ratio": {
                    "type": "string",
                    "enum": catalog.VIDEO_ASPECTS,
                    "description": "Aspect ratio of the output. Supported values differ by model (and "
                    "image-to-video often derives it from the input frame); the error lists valid values "
                    "on a mismatch.",
                },
                "generate_audio": {
                    "type": "boolean",
                    "description": "Whether to generate a synchronized audio track, on models with a native "
                    "audio toggle (most default to true). Ignored by models without one.",
                },
            },
            "required": ["prompt"],
            "additionalProperties": False,
        },
    },
    "dry_run": {
        "type": "boolean",
        "description": "If true, return the requests that would be sent (keys masked), make no API call.",
        "default": False,
    },
}
VIDEO_GENERATE_REQUIRED = ["requests"]


# ---------------------------------------------------------------------------- audio_generate
AUDIO_GENERATE_DESCRIPTION = (
    "For a user's voiceover request, load the `generating-audio` skill BEFORE calling this — it picks "
    "the right model and voice and prepares the script for reading aloud (this tool does none of that, "
    "and calling it raw gives a flat, mispronounced read). "
    "Turn written text into spoken audio: voiceovers, narration, ad reads, character lines, or any "
    "script read aloud. Pass `requests`: ONE object per clip (wrap even a single clip — "
    "`{ requests: [ { text } ] }`); add more objects (up to 10) to generate DIFFERENT lines in one "
    "call — a single approval covers the batch. Each result carries the spoken audio plus a local "
    "file `path`, or a structured error with a hint. "
    "This generates speech and nothing else: no sound effects, music, or ambience, no re-voicing an "
    "existing recording, and no dubbing a video. If the user asks for one of those, say so plainly "
    "rather than substituting a different tool. "
    "Every request needs a `voice` — the `voice_id` of a row from list_voices. There is no default "
    "voice. Models differ in expressiveness, language coverage, speed, price, and per-request "
    "character limit — call list_audio_models to compare them. Set dry_run=true to preview the exact "
    "requests without generating (no credits spent)."
)

AUDIO_GENERATE_PROPERTIES = {
    "requests": {
        "type": "array",
        "minItems": 1,
        "maxItems": 10,
        "description": "One object per audio clip (wrap even a single clip); add more objects to "
        "generate different lines in one call (up to 10).",
        "items": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Exactly what the voice will say, word for word. Everything here "
                    "is read out, so leave out anything that is a note to the reader rather than part "
                    "of the line. Write numbers, dates, and acronyms the way they should sound, and "
                    "use punctuation to place the pauses.",
                },
                "type": {
                    "type": "string",
                    "enum": catalog.AUDIO_TYPES,
                    "default": "speech",
                    "description": "The kind of audio to make. The error lists the supported "
                    "values on a mismatch.",
                },
                "model": {
                    "type": "string",
                    "default": catalog.default_model("audio"),
                    "description": f"Audio model name. Omit to use the default "
                    f"('{catalog.default_model('audio')}'). If you need to choose and don't already "
                    "have one in mind, call list_audio_models.",
                },
                "voice": {
                    "type": "string",
                    "description": "REQUIRED. The `voice_id` of a row returned by list_voices. Use "
                    "the id, never a display name. There is no default voice: the voice is chosen "
                    "for the brief, so call list_voices first.",
                },
                "speed": {
                    "type": "number",
                    "minimum": 0.7,
                    "maximum": 1.2,
                    "description": "Optional speaking-rate multiplier (1.0 = normal). Values near "
                    "either end degrade quality; rewrite to length rather than pushing it.",
                },
                "stability": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "Optional consistency of the read (higher = steadier and "
                    "flatter, lower = more varied and emotive); default 0.5. On some models it "
                    "behaves as a few coarse bands rather than a smooth dial, so move it in visible "
                    "steps. Out-of-range values are snapped, and the result reports what was used.",
                },
                "style": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "Optional style exaggeration, 0-1. Raises expressiveness at the "
                    "cost of stability; leave unset for a straight read.",
                },
                "similarity_boost": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "Optional adherence to the original voice, 0-1. Raise it when a "
                    "chosen voice drifts across a long read.",
                },
                "format": {
                    "type": "string",
                    "enum": catalog.AUDIO_FORMATS,
                    "description": "Optional output container. Omit for mp3, which is the right "
                    "choice unless something downstream needs lossless or raw audio.",
                },
            },
            "required": ["text", "voice"],
            "additionalProperties": False,
        },
    },
    "dry_run": {
        "type": "boolean",
        "description": "If true, return the requests that would be sent (keys masked), make no API call.",
        "default": False,
    },
}
AUDIO_GENERATE_REQUIRED = ["requests"]


# ---------------------------------------------------------------------------- list_audio_models
LIST_AUDIO_MODELS_DESCRIPTION = (
    "List the available speech models — for each, its strengths, price, per-request character limit, "
    "language coverage, and the audio types it supports — plus the output formats audio_generate "
    "accepts. Every model works with every voice, so voices are a separate concern — use list_voices "
    "for those. This is the authoritative source for what a model accepts; call it when choosing a "
    "model for an open-ended request, or to check a value before setting it. Pass an optional "
    "'query' to filter models by use-case keyword (e.g. 'expressive', 'long-form', 'fast')."
)

LIST_AUDIO_MODELS_PROPERTIES = {
    "query": {
        "type": "string",
        "description": "Optional keyword to filter models by use-case (matches the name, display name, and strengths).",
    },
}
LIST_AUDIO_MODELS_REQUIRED = []


# ---------------------------------------------------------------------------- list_voices
LIST_VOICES_DESCRIPTION = (
    "Find a voice to speak with, and get the `voice_id` that audio_generate requires. Returns the "
    "voices saved in the active ElevenLabs account — the user's own on their key, or the shared "
    "SuperCMO set on a managed key — each with its gender, accent, age, use-case and a "
    "`preview_url` you can hand the user so they hear it before committing. "
    "Filter by what the brief actually demands (a stated gender or accent is not negotiable) and "
    "keep `limit` small: offer a few candidates with their previews rather than a long list. "
    "A voice missing the attribute you filtered on is kept rather than dropped, because a voice the "
    "user cloned themselves often carries no labels at all. "
    "If the account holds no voices the result says so — a newly created ElevenLabs account starts "
    "empty, and voices must be added in the ElevenLabs dashboard before anything can be spoken."
)

LIST_VOICES_PROPERTIES = {
    "search": {
        "type": "string",
        "description": "Free-text match over name, description and labels (e.g. 'warm', "
        "'storyteller'). Passed to the provider.",
    },
    "gender": {
        "type": "string",
        "enum": ["male", "female", "neutral"],
        "description": "Filter by voice gender. Apply whenever the user stated one.",
    },
    "age": {
        "type": "string",
        "enum": ["young", "middle_aged", "old"],
        "description": "Filter by apparent age of the voice.",
    },
    "accent": {
        "type": "string",
        "description": "Filter by accent as the provider labels it (e.g. 'american', 'british', "
        "'indian', 'australian'). Free text, since the set grows.",
    },
    "use_case": {
        "type": "string",
        "description": "Filter by what the voice is built for (e.g. 'advertisement', "
        "'conversational', 'narrative_story', 'social_media', 'informative_educational').",
    },
    "language": {
        "type": "string",
        "description": "Filter by primary language as a short code (e.g. 'en', 'hi', 'es').",
    },
    "limit": {
        "type": "integer",
        "minimum": 1,
        "maximum": 50,
        "default": 8,
        "description": "How many voices to return. Keep it small — a handful of good candidates "
        "beats a catalogue.",
    },
}
LIST_VOICES_REQUIRED = []


# ---------------------------------------------------------------------------- job_status
JOB_STATUS_DESCRIPTION = (
    "Retrieve a long-running generation that was submitted earlier but hasn't finished — any result "
    "from a generation tool that came back as `{status:\"pending\", ...}` (a job handle, not media). "
    "Pass the exact pending handle object(s) in `jobs`; NEVER re-submit a pending job with the tool "
    "that created it — that starts (and bills) a new one. Each job comes back either finished (a "
    "hosted URL plus a local file `path`) or still `{status:\"pending\", ...}` if it isn't done yet, "
    "in which case call job_status again with the same handle after a short wait. This works for any "
    "kind of pending generation and only rejoins an existing job — it neither starts nor bills a new one."
)

JOB_STATUS_PROPERTIES = {
    "jobs": {
        "type": "array",
        "minItems": 1,
        "maxItems": 10,
        "description": "The pending job handle object(s) to retrieve — each exactly as returned by a "
        "prior video_generate / job_status call. Add more than one to retrieve a batch in one call.",
        "items": {"type": "object", "additionalProperties": True},
    },
}
JOB_STATUS_REQUIRED = ["jobs"]


# ---------------------------------------------------------------------------- list_video_models
LIST_VIDEO_MODELS_DESCRIPTION = (
    "List the available video-generation models with, for each, its full schema: modes (text / image / "
    "first-last-frame / reference), the aspect ratios, durations and resolutions it accepts, which media it "
    "takes (start/end frame and reference image/video/audio with max counts), whether it has native audio, "
    "plus strengths and price. This is the authoritative source for a model's exact ranges — call it when "
    "choosing a model for an open-ended request, or to check what a model accepts before setting "
    "aspect_ratio / duration / resolution / media. Pass an optional 'query' to filter by use-case keyword "
    "(e.g. 'cinematic', 'fast', 'audio')."
)

LIST_VIDEO_MODELS_PROPERTIES = {
    "query": {
        "type": "string",
        "description": "Optional keyword to filter models by use-case (matches the name, display name, and strengths).",
    },
}
LIST_VIDEO_MODELS_REQUIRED = []


# ---------------------------------------------------------------------------- video_stitch
VIDEO_STITCH_DESCRIPTION = (
    "Join finished video clips into one file, in the order given, with a hard cut between each and "
    "each clip's audio kept — this assembles existing clips, it does not generate new video. Use it "
    "to build a video longer than a single model clip: generate the shots with video_generate, then "
    "stitch them. Do NOT use it for a single clip, or for a batch of clips meant to stay separate. "
    "Optionally lay a background-music track under the whole thing (pass `music`) or burn in "
    "subtitles from an SRT file (pass `subtitles`); clips of different sizes are scaled to a common "
    "frame. Returns the output file `path` with its duration, resolution, and size, or a structured "
    "error with a hint. Requires ffmpeg on the system. Set dry_run=true to preview the plan without "
    "running anything."
)

VIDEO_STITCH_PROPERTIES = {
    "clips": {
        "type": "array",
        "items": {"type": "string"},
        "minItems": 2,
        "description": "The clips to join, in play order — local file paths (e.g. the `path` a "
        "video_generate result returns) or direct http(s) video URLs. At least two.",
    },
    "music": {
        "type": "string",
        "description": "Optional audio file (a local path or a URL) laid under the whole video as "
        "background music, mixed below the clips' own audio.",
    },
    "subtitles": {
        "type": "string",
        "description": "Optional SRT subtitle file (a local path or a URL) burned into the video.",
    },
    "output": {
        "type": "string",
        "description": "Optional output file path. Omit to write a default filename into the media "
        "output directory.",
    },
    "dry_run": {
        "type": "boolean",
        "description": "If true, return the planned output path and inputs; run no ffmpeg.",
        "default": False,
    },
}
VIDEO_STITCH_REQUIRED = ["clips"]
