"""Video stitching tool — thin MCP binding over supercmo_skills.

Joins finished video clips into one file with `ffmpeg` (local, no vendor API, no key). All the
assembly logic lives in supercmo_skills; the schema lives once in tool_specs.
"""

from .. import registry
import supercmo_skills
from supercmo_skills import tool_specs


VIDEO_STITCH = {
    "name": "video_stitch",
    "description": tool_specs.VIDEO_STITCH_DESCRIPTION,
    "inputSchema": tool_specs.object_schema(
        tool_specs.VIDEO_STITCH_PROPERTIES, tool_specs.VIDEO_STITCH_REQUIRED),
}


def video_stitch(args):
    return supercmo_skills.video_stitch(
        clips=args.get("clips"),
        music=args.get("music"),
        subtitles=args.get("subtitles"),
        narration=args.get("narration"),
        output=args.get("output"),
        dry_run=bool(args.get("dry_run", False)),
    )


registry.register(VIDEO_STITCH, video_stitch)
