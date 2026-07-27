"""supercmo_skills — the one media client both bindings (MCP server + OSS Hermes tool)
and the hosted proxy import. Stdlib-only so it vendors into the Claude plugin with no
install step, and publishes as a PyPI package for the OSS app + proxy.

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
    image_analysis, image_generate, text_to_speech, url_extraction, video_generate)

__all__ = ["image_generate", "video_generate", "text_to_speech", "url_extraction",
           "image_analysis", "catalog"]
