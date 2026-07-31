"""Setup-status tool — thin MCP binding over supercmo_skills.readiness.

Reports which media keys are configured and which capabilities are ready, so any host (Claude Code,
Cursor, Codex) can check setup identically with ZERO path knowledge — no `python3 scripts/doctor.py`.
All logic lives in supercmo_skills.readiness; this only declares the schema and forwards.
"""
import os
import sys

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(PLUGIN_ROOT, "scripts"))

import registry  # noqa: E402
from supercmo_skills import readiness  # noqa: E402


SETUP_STATUS = {
    "name": "setup_status",
    "description": (
        "Check which SuperCMO media-generation keys are configured and which capabilities "
        "(image / video / audio) are ready — the setup doctor. Call this FIRST when a user is "
        "setting up SuperCMO, asks which keys they need, or a generation failed with "
        "'no_provider_configured'. Returns each vendor key (set/missing, what it enables, where to "
        "get it), managed-key state, and per-capability readiness. Set check=true for a FREE "
        "key-validity probe where one exists (never a paid generation). Reports only key NAMES and "
        "set/missing — never key values."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "check": {
                "type": "boolean",
                "description": "If true, also run a FREE key-validity probe where a provider implements one (no paid call).",
                "default": False,
            },
        },
        "additionalProperties": False,
    },
}


def setup_status(args):
    return readiness.status(check=bool(args.get("check", False)))


registry.register(SETUP_STATUS, setup_status)
