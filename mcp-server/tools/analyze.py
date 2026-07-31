"""Image analysis (vision) tool — thin MCP binding over supercmo_skills.

Reads an image (local path or URL) and answers a question about it (Gemini vision under the hood).
All routing/vendor logic lives in supercmo_skills; this only declares the schema and forwards.
"""
import os
import sys

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(PLUGIN_ROOT, "scripts"))

import registry  # noqa: E402
import supercmo_skills  # noqa: E402


IMAGE_ANALYSIS = {
    "name": "image_analysis",
    "description": (
        "Look at an image (a local file path or an image URL) and answer a question about it — "
        "returns text, not a new image. Use to read a product photo (category, materials, on-pack "
        "text, distinctive details), to judge whether a shot is product-only or shows a face, or to "
        "describe any image's content, layout, or text. Give a specific 'prompt' for a focused "
        "answer; omit it for a general description. Set dry_run=true to preview the request without "
        "spending."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "image": {
                "type": "string",
                "description": "The image to analyze — a local file path or an http(s) image URL.",
            },
            "prompt": {
                "type": "string",
                "description": "The question to answer about the image — e.g. 'What product is this, "
                "how is it used, how does it open, and what color/material/label details define it?' "
                "Omit for a general description.",
            },
            "dry_run": {
                "type": "boolean",
                "description": "If true, return the request that would be sent (key and image masked), make no API call.",
                "default": False,
            },
        },
        "required": ["image"],
        "additionalProperties": False,
    },
}


def image_analysis(args):
    return supercmo_skills.image_analysis(
        image=args.get("image"),
        prompt=args.get("prompt"),
        dry_run=bool(args.get("dry_run", False)),
    )


registry.register(IMAGE_ANALYSIS, image_analysis)


VIDEO_ANALYSIS = {
    "name": "video_analysis",
    "description": (
        "Watch a video (a local file path or a video URL) and answer a question about it — returns "
        "text, not a new video. Use to read a supplied or reference clip before generating: its "
        "subject and setting, the key actions, the camera work and motion, the pacing, and the gist "
        "of any audio, so a new prompt can animate or match it instead of contradicting it. Give a "
        "specific 'prompt' for a focused answer; omit it for a general breakdown. Analyzes a clip "
        "inline, so a very large file may be rejected — trim or link a shorter clip if so. Set "
        "dry_run=true to preview the request without spending."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "video": {
                "type": "string",
                "description": "The video to analyze — a local file path or an http(s) video URL.",
            },
            "prompt": {
                "type": "string",
                "description": "The question to answer about the video — e.g. 'What happens, and what "
                "camera movement, pacing, and audio does it use?' Omit for a general breakdown.",
            },
            "dry_run": {
                "type": "boolean",
                "description": "If true, return the request that would be sent (key and video masked), make no API call.",
                "default": False,
            },
        },
        "required": ["video"],
        "additionalProperties": False,
    },
}


def video_analysis(args):
    return supercmo_skills.video_analysis(
        video=args.get("video"),
        prompt=args.get("prompt"),
        dry_run=bool(args.get("dry_run", False)),
    )


registry.register(VIDEO_ANALYSIS, video_analysis)
