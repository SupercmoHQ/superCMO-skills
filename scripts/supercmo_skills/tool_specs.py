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
    "Each entry in `results` is one of three things: finished media; a "
    "`{status:\"pending\", ...}` job handle to rejoin with job_status; or a failure carrying "
    "`ok: false` and an `error`. A failed entry is terminal — report its `error` and never "
    "poll or re-submit it. Read every entry rather than the top-level counters alone."
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
                    "description": "Aspect ratio of the output image. Support differs per model — "
                    f"every model accepts {', '.join(catalog.IMAGE_ASPECTS_COMMON)}; the wider ratios "
                    "are model-specific. Call list_image_models for the set a given model accepts.",
                },
                "resolution": {
                    "type": "string",
                    "enum": catalog.IMAGE_RESOLUTIONS,
                    "default": catalog.IMAGE_DEFAULT_RESOLUTION,
                    "description": "Output resolution tier. Models differ in which tiers they render at — asking for one a model cannot render is an error naming the tiers it accepts, never a silent downgrade. call list_image_models for a model's tiers.",
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
    "List the available image-generation models (with strengths, price, the aspect ratios each "
    "accepts and how many reference images it takes), plus the valid aspect ratios and resolution "
    "tiers that image_generate accepts. Use when you need to "
    "choose a model and don't already have one in mind (e.g. an open-ended request), or to "
    "check the valid aspect_ratio / resolution values, or how many reference images a model will "
    "take, before calling image_generate — most of the time the model is the "
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
    "Each entry in `results` is one of three things: finished media; a "
    "`{status:\"pending\", ...}` job handle to rejoin with job_status; or a failure carrying "
    "`ok: false` and an `error`. A failed entry is terminal — report its `error` and never "
    "poll or re-submit it. Read every entry rather than the top-level counters alone."
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
    "Each entry in `results` is one of three things: finished media; a "
    "`{status:\"pending\", ...}` job handle to rejoin with job_status; or a failure carrying "
    "`ok: false` and an `error`. A failed entry is terminal — report its `error` and never "
    "poll or re-submit it. Read every entry rather than the top-level counters alone."
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
    "that created it — that starts (and bills) a new one. Each job comes back one of three ways: "
    "**finished** (a hosted URL plus a local file `path`); still **pending** (`{status:\"pending\", "
    "...}`), in which case call job_status again with the same handle after a short wait; or "
    "**failed**, carrying `ok: false` and an `error`. A failed job is terminal — it will never "
    "finish, so report the error and never poll or re-submit that handle. A batch can mix all three, "
    "so read every entry in `results` rather than the top-level counters alone. This works for any "
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
    "Three optional layers, each its own parameter: lay a voiceover over the picture (pass "
    "`narration` — ONE take per clip, in clip order, NOT one joined track; each take is aligned to "
    "its own clip so nothing drifts), lay a background-music track under the whole thing (pass "
    "`music`), or burn in subtitles from an SRT file (pass `subtitles`); clips of different sizes "
    "are scaled to a common frame. Returns the output file `path` with its duration, resolution, "
    "and size, or a structured "
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
    "narration": {
        "type": "array",
        "items": {"type": "string"},
        "description": "Optional voiceover — ONE audio take per clip, in the same order and the same "
        "count as `clips`. Each take is padded with silence to its clip's length, so take N is heard "
        "over clip N with no timecodes to keep in sync. The narration sits at full level and the "
        "clips' own audio is ducked beneath it. A take longer than the clip it belongs to is an "
        "error naming that clip, never a truncation — shorten the line and re-voice that one take.",
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


# ---------------------------------------------------------------------------- caption_video
CAPTION_VIDEO_DESCRIPTION = (
    "Burn styled, social-style captions into a video from a word-timed transcript — local ffmpeg, "
    "no credits. The usual chain is transcribe -> caption_video: run transcribe on the video (or its "
    "voiceover) to get word timestamps, then pass those here. Captions are styled and positioned "
    "with a font bundled in the package (no system-font dependency); optional karaoke highlights each "
    "word as it is spoken. Timestamps are relative to the video's own audio (t=0). Returns the "
    "output file `path` with its duration, resolution, and size, or a structured error with a hint. "
    "Requires ffmpeg. Set dry_run=true to preview without rendering."
)

CAPTION_VIDEO_PROPERTIES = {
    "video": {
        "type": "string",
        "description": "The video to caption — a local file path (e.g. a video_generate `path`) or "
        "an http(s) video URL.",
    },
    "transcript": {
        "type": "array",
        "minItems": 1,
        "description": "The words to show, in order — each an object with the word text and its "
        "timing in seconds. This is exactly the `words` list transcribe returns.",
        "items": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The word (or `word` is also accepted)."},
                "start": {"type": "number", "description": "Word start time in seconds."},
                "end": {"type": "number", "description": "Word end time in seconds."},
            },
            "required": ["start", "end"],
            "additionalProperties": True,
        },
    },
    "style": {
        "type": "object",
        "description": "Optional caption styling.",
        "properties": {
            "font_size": {"type": "integer", "description": "Font size in pixels. Omit for ~6% of the video height."},
            "primary_color": {"type": "string", "description": "Text colour, #RRGGBB (default white)."},
            "highlight_color": {"type": "string", "description": "Karaoke highlight colour, #RRGGBB (default #FFE600)."},
            "outline_color": {"type": "string", "description": "Outline colour, #RRGGBB (default black)."},
            "position": {"type": "string", "enum": ["bottom", "center", "top"], "description": "Vertical placement (default bottom)."},
            "words_per_line": {"type": "integer", "description": "Words per caption line (default 5)."},
            "karaoke": {"type": "boolean", "description": "Highlight each word as spoken (default true)."},
            "bold": {"type": "boolean", "description": "Bold text (default true)."},
        },
        "additionalProperties": False,
    },
    "output": {
        "type": "string",
        "description": "Optional output file path. Omit to write a default filename into the media output directory.",
    },
    "dry_run": {
        "type": "boolean",
        "description": "If true, return the planned output and line count; run no ffmpeg.",
        "default": False,
    },
}
CAPTION_VIDEO_REQUIRED = ["video", "transcript"]


# ---------------------------------------------------------------------------- video_overlay
VIDEO_OVERLAY_DESCRIPTION = (
    "Stamp a logo, timed text, and a branded end card onto a video — local ffmpeg, no credits. "
    "Overlay a logo watermark at a chosen corner, drop in timed text (CTAs, offers, captions you "
    "place yourself), and/or append an end-card image as a short closing still. Pass at least one "
    "of logo / texts / end_card. Text is rendered with a bundled font (no system-font dependency). "
    "Returns the output file `path` with its duration and resolution, or a structured error. "
    "Requires ffmpeg. Set dry_run=true to preview."
)

VIDEO_OVERLAY_PROPERTIES = {
    "video": {
        "type": "string",
        "description": "The video to decorate — a local file path or an http(s) video URL.",
    },
    "logo": {
        "type": "string",
        "description": "Optional logo image (PNG with transparency recommended) — path or URL.",
    },
    "logo_position": {
        "type": "string",
        "enum": ["top-left", "top-right", "bottom-left", "bottom-right", "center"],
        "description": "Where the logo sits (default bottom-right).",
        "default": "bottom-right",
    },
    "logo_scale": {
        "type": "number",
        "description": "Logo width as a fraction of the video width (default 0.15).",
    },
    "texts": {
        "type": "array",
        "description": "Timed text overlays.",
        "items": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The text to show."},
                "start": {"type": "number", "description": "Start time in seconds."},
                "end": {"type": "number", "description": "End time in seconds."},
                "position": {"type": "string", "enum": ["top", "center", "bottom", "top-left", "top-right", "bottom-left", "bottom-right"], "description": "Placement (default center)."},
                "color": {"type": "string", "description": "Text colour #RRGGBB (default white)."},
                "font_size": {"type": "integer", "description": "Font size in pixels (default ~5% of height)."},
            },
            "required": ["text", "start", "end"],
            "additionalProperties": False,
        },
    },
    "end_card": {
        "type": "string",
        "description": "Optional end-card image (path or URL) appended as a closing still.",
    },
    "end_card_duration": {
        "type": "number",
        "description": "How long the end card holds, in seconds (default 3).",
    },
    "output": {
        "type": "string",
        "description": "Optional output file path. Omit to write a default filename into the media output directory.",
    },
    "dry_run": {
        "type": "boolean",
        "description": "If true, return the plan; run no ffmpeg.",
        "default": False,
    },
}
VIDEO_OVERLAY_REQUIRED = ["video"]


# ---------------------------------------------------------------------------- transcribe
TRANSCRIBE_DESCRIPTION = (
    "Transcribe speech from an audio or video file into text with word-level timestamps. Use it to "
    "caption a video (chain transcribe -> caption_video), to read a voiceover back, or to analyse a "
    "competitor ad's spoken script. `audio` is a local file path or an http(s) URL (audio or "
    "video). Returns {ok, text, words:[{word, start, end}], duration, language}, or a structured "
    "error. Set dry_run=true to preview the request without spending."
)

TRANSCRIBE_PROPERTIES = {
    "audio": {
        "type": "string",
        "description": "The audio or video to transcribe — a local file path or an http(s) URL.",
    },
    "language": {
        "type": "string",
        "description": "Optional ISO language-code hint (e.g. 'en'); omit to auto-detect.",
    },
    "dry_run": {
        "type": "boolean",
        "description": "If true, preview the request (key masked); make no API call.",
        "default": False,
    },
}
TRANSCRIBE_REQUIRED = ["audio"]


# ---------------------------------------------------------------------------- social_research
SOCIAL_RESEARCH_DESCRIPTION = (
    "Pull read-only structured public data from social platforms and ad libraries — competitor ads "
    "(Meta/Facebook + Instagram, LinkedIn), profiles, posts, comments, transcripts, hashtag/keyword "
    "search, and subreddit / trend discovery. Two steps: call list_research_sources FIRST to see the "
    "platforms, their endpoints, and each endpoint's params; then call this with `platform`, "
    "`endpoint`, and a `params` object built from that endpoint's required/optional params. Returns "
    "the source's structured JSON in `data` (the shape varies by endpoint), or a structured error "
    "naming the missing or unknown params. Use for competitor and market research, audience "
    "listening, and trend discovery — this is read-only public data, not posting and not private "
    "data. Set dry_run=true to preview the exact request without spending."
)

SOCIAL_RESEARCH_PROPERTIES = {
    "platform": {
        "type": "string",
        "description": "The platform to query — e.g. 'meta_ad_library', 'instagram', 'tiktok', "
        "'youtube', 'reddit', 'x', 'linkedin', 'linkedin_ads'. Call list_research_sources for the "
        "full set.",
    },
    "endpoint": {
        "type": "string",
        "description": "The endpoint on that platform — e.g. 'company_ads', 'profile', 'posts', "
        "'comments', 'search', 'hashtag'. Call list_research_sources for each platform's endpoints.",
    },
    "params": {
        "type": "object",
        "description": "The endpoint's query parameters as an object — e.g. {\"handle\": \"nike\"} or "
        "{\"companyName\": \"Nike\", \"country\": \"US\"}. list_research_sources lists the required and "
        "optional params for each endpoint; a missing required param returns a structured error.",
        "additionalProperties": True,
    },
    "dry_run": {
        "type": "boolean",
        "description": "If true, return the request that would be sent (key masked), make no API call.",
        "default": False,
    },
}
SOCIAL_RESEARCH_REQUIRED = ["platform", "endpoint"]


# ---------------------------------------------------------------------------- list_research_sources
LIST_RESEARCH_SOURCES_DESCRIPTION = (
    "List the available research sources for social_research — every platform, its endpoints, and "
    "each endpoint's required and optional params plus per-call cost. Call this FIRST whenever you "
    "need competitor ads, profiles, posts, comments, transcripts, or platform search and don't "
    "already know the exact platform + endpoint + params. Pass an optional 'query' to filter by "
    "platform, endpoint, or keyword (e.g. 'ads', 'reddit', 'comments')."
)

LIST_RESEARCH_SOURCES_PROPERTIES = {
    "query": {
        "type": "string",
        "description": "Optional keyword to filter sources by platform, endpoint, or description.",
    },
}
LIST_RESEARCH_SOURCES_REQUIRED = []
