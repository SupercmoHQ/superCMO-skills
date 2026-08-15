"""Audio-mixing tool — thin MCP binding over supercmo_skills.

Mixes a voiceover, music bed, and sound effects with `ffmpeg` (local, no vendor API, no key). The
mix logic lives in supercmo_skills; the schema lives once in tool_specs.
"""

from .. import registry
import supercmo_skills
from supercmo_skills import tool_specs


AUDIO_MIX = {
    "name": "audio_mix",
    "description": tool_specs.AUDIO_MIX_DESCRIPTION,
    "inputSchema": tool_specs.object_schema(
        tool_specs.AUDIO_MIX_PROPERTIES, tool_specs.AUDIO_MIX_REQUIRED),
}


def audio_mix(args):
    return supercmo_skills.audio_mix(
        voice=args.get("voice"),
        video=args.get("video"),
        music=args.get("music"),
        sfx=args.get("sfx"),
        music_gain=args.get("music_gain"),
        duck=bool(args.get("duck", True)),
        format=args.get("format"),
        output=args.get("output"),
        dry_run=bool(args.get("dry_run", False)),
    )


registry.register(AUDIO_MIX, audio_mix)
