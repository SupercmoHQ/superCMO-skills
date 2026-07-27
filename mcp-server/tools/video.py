"""Video generation tools — thin MCP binding over supercmo_skills.

The tool name (`video_generate`) and args match the OSS app's custom tool and Hermes's
native tool name, so one SKILL.md drives both runtimes. All catalog + routing + vendor
logic lives in supercmo_skills.
"""
import os
import sys

# supercmo_skills lives in the plugin's scripts/ dir (repo_root/scripts).
PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(PLUGIN_ROOT, "scripts"))

import registry  # noqa: E402
import supercmo_skills  # noqa: E402
from supercmo_skills import catalog  # noqa: E402

ASPECTS = catalog.ASPECTS
DEFAULT_MODEL = catalog.default_model("video")


VIDEO_GENERATE = {
    "name": "video_generate",
    "description": (
        "Generate a short video clip from a text prompt, optionally animating a still image "
        "or guided by reference images (a product, a character, a style to follow). Returns a "
        "hosted video URL plus metadata (model, seed, duration), and saves the video to a local "
        "file (absolute path in the 'path' field). Use when the user wants to create video ads, product motion, "
        "animated concepts, or b-roll from a description, or to bring a supplied image to life. "
        "Pass image_url to animate a single starting frame, or reference_images (local file "
        "paths or URLs) to guide the result; when present, the prompt should describe the desired "
        "motion and refer to the supplied reference(s). Set dry_run=true to preview the exact "
        "request and cost without generating (no credits spent)."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "The video description. Be specific about subject, motion, style, and pacing.",
            },
            "model": {
                "type": "string",
                "default": DEFAULT_MODEL,
                "description": f"Video model name. Omit to use the default ('{DEFAULT_MODEL}'). "
                "Pass a specific model when one is called for; if you need to choose and don't "
                "already have one in mind, call list_video_models to browse the options.",
            },
            "image_url": {
                "type": "string",
                "description": "Optional starting frame to animate — a local file path or an image URL. "
                "Use for image-to-video; omit for pure text-to-video.",
            },
            "reference_images": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional reference image(s) to guide the result — each a local file "
                "path or an image URL. Use for product/character-driven generation or to follow a "
                "supplied style. If a model rejects the count, the error states its limit.",
            },
            "duration": {
                "type": "integer",
                "description": "Clip length in seconds (default 8).",
                "default": 8,
            },
            "resolution": {
                "type": "string",
                "default": "720p",
                "description": "Output resolution (default '720p').",
            },
            "aspect_ratio": {
                "type": "string",
                "enum": ASPECTS,
                "default": catalog.DEFAULT_ASPECT,
                "description": "Aspect ratio of the output video.",
            },
            "generate_audio": {
                "type": "boolean",
                "description": "Whether to generate an audio track alongside the video, when the model supports it.",
            },
            "seed": {
                "type": "integer",
                "description": "Optional seed for reproducibility.",
            },
            "dry_run": {
                "type": "boolean",
                "description": "If true, return the request that would be sent (key masked), make no API call.",
                "default": False,
            },
        },
        "required": ["prompt"],
        "additionalProperties": False,
    },
}


def video_generate(args):
    return supercmo_skills.video_generate(
        prompt=args.get("prompt"),
        model=args.get("model"),
        image_url=args.get("image_url"),
        reference_images=args.get("reference_images"),
        duration=int(args["duration"]) if args.get("duration") is not None else None,
        resolution=args.get("resolution"),
        aspect_ratio=args.get("aspect_ratio"),
        generate_audio=args.get("generate_audio"),
        seed=int(args["seed"]) if args.get("seed") is not None else None,
        dry_run=bool(args.get("dry_run", False)),
    )


registry.register(VIDEO_GENERATE, video_generate)


LIST_VIDEO_MODELS = {
    "name": "list_video_models",
    "description": (
        "List the available video-generation models with their strengths and price. Use only "
        "when you need to choose a model for video_generate and don't already have one in mind "
        "(e.g. an open-ended request) — most of the time the model is the default or is already "
        "specified. Pass an optional 'query' to filter by use-case keyword (e.g. 'fast', "
        "'cinematic', 'audio')."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Optional keyword to filter models by use-case (matches the name, display name, and strengths).",
            },
        },
        "additionalProperties": False,
    },
}


def list_video_models(args):
    return {"ok": True, "default": catalog.default_model("video"), "aspect_ratios": catalog.ASPECTS,
            "models": catalog.list_models("video", args.get("query"))}


registry.register(LIST_VIDEO_MODELS, list_video_models)
