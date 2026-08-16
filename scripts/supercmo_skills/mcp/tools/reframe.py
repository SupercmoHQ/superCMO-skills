"""Reframe tool — thin MCP binding over supercmo_skills.

Converts a video's aspect ratio with `ffmpeg` (local, no vendor API, no key). The reframe logic
lives in supercmo_skills; the schema lives once in tool_specs.
"""

from .. import registry
import supercmo_skills
from supercmo_skills import tool_specs


REFRAME = {
    "name": "reframe",
    "description": tool_specs.REFRAME_DESCRIPTION,
    "inputSchema": tool_specs.object_schema(
        tool_specs.REFRAME_PROPERTIES, tool_specs.REFRAME_REQUIRED),
}


def reframe(args):
    return supercmo_skills.reframe(
        video=args.get("video"),
        aspect=args.get("aspect"),
        mode=args.get("mode") or "crop",
        focus=args.get("focus"),
        output=args.get("output"),
        dry_run=bool(args.get("dry_run", False)),
    )


registry.register(REFRAME, reframe)
