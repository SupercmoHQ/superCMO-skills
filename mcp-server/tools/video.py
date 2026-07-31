"""Video generation tools — thin MCP binding over supercmo_skills.

The tool name (`video_generate`) matches the OSS app's custom tool so one SKILL.md drives it. All
catalog + routing + vendor logic lives in supercmo_skills; the schema lives once in tool_specs.
"""
import os
import sys
from concurrent.futures import ThreadPoolExecutor

# supercmo_skills lives in the plugin's scripts/ dir (repo_root/scripts).
PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(PLUGIN_ROOT, "scripts"))

import registry  # noqa: E402
import supercmo_skills  # noqa: E402
from supercmo_skills import catalog, tool_specs  # noqa: E402


VIDEO_GENERATE = {
    "name": "video_generate",
    "description": tool_specs.VIDEO_GENERATE_DESCRIPTION,
    "inputSchema": tool_specs.object_schema(
        tool_specs.VIDEO_GENERATE_PROPERTIES, tool_specs.VIDEO_GENERATE_REQUIRED),
}


def video_generate(args):
    reqs = args.get("requests")
    dry_run = bool(args.get("dry_run", False))
    if not isinstance(reqs, list) or not reqs:
        return {"ok": False, "error": "requests must be a non-empty list of video request objects (1-10)."}
    if len(reqs) > 10:
        return {"ok": False, "error": f"at most 10 requests per call; got {len(reqs)}.",
                "hint": "split into more calls"}

    def _one(r):
        if not isinstance(r, dict) or not r.get("prompt"):
            return {"ok": False, "error": "each request must be an object with a prompt."}
        return supercmo_skills.video_generate(
            prompt=r.get("prompt"), model=r.get("model"),
            start_frame_image=r.get("start_frame_image"), end_frame_image=r.get("end_frame_image"),
            reference_images=r.get("reference_images"), reference_videos=r.get("reference_videos"),
            reference_audios=r.get("reference_audios"),
            duration=(int(r["duration"]) if r.get("duration") is not None else None),
            resolution=r.get("resolution"), aspect_ratio=r.get("aspect_ratio"),
            generate_audio=r.get("generate_audio"), dry_run=dry_run)

    # Each request submits then waits on its own thread, so a batch's clips are generated
    # concurrently — wall time ≈ the slowest clip, not their sum. A clip slower than one wait window
    # comes back as a pending handle; rejoin it with job_status.
    if dry_run or len(reqs) == 1:
        results = [_one(r) for r in reqs]
    else:
        with ThreadPoolExecutor(max_workers=min(8, len(reqs))) as ex:
            results = list(ex.map(_one, reqs))
    pending = sum(1 for r in results if supercmo_skills.is_pending(r))
    out = {"ok": all(supercmo_skills.job_ok(x) for x in results), "count": len(results), "results": results}
    if pending:
        out["pending"] = pending
        out["hint"] = "some clips are still generating — call job_status with each pending clip's job handle to retrieve it (do not re-submit)."
    return out


registry.register(VIDEO_GENERATE, video_generate)


LIST_VIDEO_MODELS = {
    "name": "list_video_models",
    "description": tool_specs.LIST_VIDEO_MODELS_DESCRIPTION,
    "inputSchema": tool_specs.object_schema(
        tool_specs.LIST_VIDEO_MODELS_PROPERTIES, tool_specs.LIST_VIDEO_MODELS_REQUIRED),
}


def list_video_models(args):
    return catalog.video_models_listing(args.get("query"))


registry.register(LIST_VIDEO_MODELS, list_video_models)
