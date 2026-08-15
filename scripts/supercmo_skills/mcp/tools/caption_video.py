"""Caption-burning tool — thin MCP binding over supercmo_skills.

Burns styled captions into a video with `ffmpeg` + libass (local, no vendor API, no key). The
render logic lives in supercmo_skills; the schema lives once in tool_specs.
"""

from .. import registry
import supercmo_skills
from supercmo_skills import tool_specs


CAPTION_VIDEO = {
    "name": "caption_video",
    "description": tool_specs.CAPTION_VIDEO_DESCRIPTION,
    "inputSchema": tool_specs.object_schema(
        tool_specs.CAPTION_VIDEO_PROPERTIES, tool_specs.CAPTION_VIDEO_REQUIRED),
}


def caption_video(args):
    return supercmo_skills.caption_video(
        video=args.get("video"),
        transcript=args.get("transcript"),
        style=args.get("style"),
        output=args.get("output"),
        dry_run=bool(args.get("dry_run", False)),
    )


registry.register(CAPTION_VIDEO, caption_video)
