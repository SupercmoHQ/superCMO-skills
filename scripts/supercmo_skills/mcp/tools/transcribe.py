"""Transcription tool — thin MCP binding over supercmo_skills.

Speech-to-text with word-level timestamps. Routing (BYOK-direct vs managed proxy) and the vendor
call live in supercmo_skills; the schema lives once in tool_specs.
"""

from .. import registry
import supercmo_skills
from supercmo_skills import tool_specs


TRANSCRIBE = {
    "name": "transcribe",
    "description": tool_specs.TRANSCRIBE_DESCRIPTION,
    "inputSchema": tool_specs.object_schema(
        tool_specs.TRANSCRIBE_PROPERTIES, tool_specs.TRANSCRIBE_REQUIRED),
}


def transcribe(args):
    return supercmo_skills.transcribe(
        audio=args.get("audio"),
        language=args.get("language"),
        dry_run=bool(args.get("dry_run", False)),
    )


registry.register(TRANSCRIBE, transcribe)
