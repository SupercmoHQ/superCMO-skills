"""Video-overlay tool — thin MCP binding over supercmo_skills.

Stamps a logo, timed text, and an end card onto a video with `ffmpeg` + libass (local, no vendor
API, no key). The overlay logic lives in supercmo_skills; the schema lives once in tool_specs.
"""

from .. import registry
import supercmo_skills
from supercmo_skills import tool_specs


VIDEO_OVERLAY = {
    "name": "video_overlay",
    "description": tool_specs.VIDEO_OVERLAY_DESCRIPTION,
    "inputSchema": tool_specs.object_schema(
        tool_specs.VIDEO_OVERLAY_PROPERTIES, tool_specs.VIDEO_OVERLAY_REQUIRED),
}


def video_overlay(args):
    return supercmo_skills.video_overlay(
        video=args.get("video"),
        logo=args.get("logo"),
        logo_position=args.get("logo_position") or "bottom-right",
        logo_scale=args.get("logo_scale") if args.get("logo_scale") is not None else 0.15,
        texts=args.get("texts"),
        end_card=args.get("end_card"),
        end_card_duration=args.get("end_card_duration") if args.get("end_card_duration") is not None else 3.0,
        output=args.get("output"),
        dry_run=bool(args.get("dry_run", False)),
    )


registry.register(VIDEO_OVERLAY, video_overlay)
