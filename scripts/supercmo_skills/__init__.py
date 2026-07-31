"""supercmo_skills — the media client the MCP server and the hosted proxy import.
Stdlib-only so it vendors into the Claude plugin with no install step, and publishes
as a PyPI package.

Provider-blind to the agent: callers pass a model string; routing (BYOK-direct > managed
proxy) and vendor translation live here, never in the tool/skill layer.
"""
import os as _os
import sys as _sys

# Make the sibling stdlib module `supercmo_env` importable (it lives in scripts/, our parent).
_sys.path.insert(0, _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))))
import supercmo_env  # noqa: E402,F401

from . import catalog  # noqa: E402
from .client import (  # noqa: E402
    audio_generate, image_analysis, image_generate, is_pending, job_ok, job_status,
    list_voices, url_extraction, video_analysis, video_generate)
from .stitch import video_stitch  # noqa: E402

__all__ = ["image_generate", "video_generate", "audio_generate", "list_voices", "url_extraction",
           "image_analysis", "video_analysis", "video_stitch", "job_status",
           "job_ok", "is_pending", "catalog"]
