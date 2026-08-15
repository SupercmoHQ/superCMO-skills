"""supercmo_skills — the media client the MCP server and the hosted proxy import.
Stdlib-only so it vendors into the Claude plugin with no install step, and publishes
as a PyPI package.

Provider-blind to the agent: callers pass a model string; routing (BYOK-direct > managed
proxy) and vendor translation live here, never in the tool/skill layer.
"""
# `supercmo_env` is a top-level module of this distribution (the wheel force-includes it; a dev
# tree puts it on the path via PYTHONPATH=scripts). Package code imports it as a normal top-level
# module — a library must never mutate sys.path on import, so there is no path setup here.
from . import catalog
from .client import (
    audio_generate, batch_envelope, image_analysis, image_generate, is_pending, job_ok, job_status,
    list_voices, max_parallel, social_research, transcribe, url_extraction, video_analysis,
    video_generate)
from .stitch import video_stitch
from .caption_video import caption_video
from .audio_mix import audio_mix
from .reframe import reframe
from .video_overlay import video_overlay

__all__ = ["image_generate", "video_generate", "audio_generate", "list_voices", "url_extraction",
           "image_analysis", "video_analysis", "video_stitch", "caption_video", "audio_mix",
           "reframe", "video_overlay", "transcribe", "job_status", "social_research", "job_ok",
           "is_pending", "batch_envelope", "max_parallel", "catalog"]
