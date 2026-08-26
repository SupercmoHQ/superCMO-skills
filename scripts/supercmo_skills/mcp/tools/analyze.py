"""Vision analysis tools — thin MCP binding over supercmo_skills.

Reads an image or a video (local path or URL) and answers a question about it (Gemini vision under
the hood). All routing/vendor logic lives in supercmo_skills; the schema lives once in tool_specs.

Both tools take EITHER a single asset (`image` / `video`) or a `requests` list of up to 10. The
batch form fans out on threads, so N assets cost about the wall time of the slowest one instead of
their sum — the stdio server handles one JSON-RPC line at a time, so N separate tool calls would
otherwise run strictly one after another.
"""
from concurrent.futures import ThreadPoolExecutor

from .. import registry
import supercmo_skills
from supercmo_skills import tool_specs


def _batch(args, key, one, noun):
    """Shared body for both tools: validate, fan out, envelope.

    Returns the single-asset result unwrapped (so existing callers see the same shape they always
    have) and a batch envelope only when `requests` was supplied."""
    reqs = args.get("requests")
    dry_run = bool(args.get("dry_run", False))
    solo = args.get(key)

    if reqs is None:
        if not solo:
            return {"ok": False, "error": f"{key} is required — pass one {key}, or a `requests` list."}
        return one({key: solo, "prompt": args.get("prompt")}, dry_run)

    if solo:
        return {"ok": False, "error": f"pass either {key} or requests, not both."}
    if not isinstance(reqs, list) or not reqs:
        return {"ok": False, "error": f"requests must be a non-empty list of {noun} request objects (1-10)."}
    if len(reqs) > 10:
        return {"ok": False, "error": f"at most 10 requests per call; got {len(reqs)}.",
                "hint": "split into more calls"}

    def _run(r):
        if not isinstance(r, dict) or not r.get(key):
            return {"ok": False, "error": f"each request must be an object with a {key}."}
        try:
            return one(r, dry_run)
        except Exception as e:
            # A raise inside the pool surfaces when results are iterated and would take the whole
            # batch with it — including the entries that already succeeded and were paid for.
            return {"ok": False, "error": f"{type(e).__name__}: {e}"}

    if dry_run or len(reqs) == 1:
        results = [_run(r) for r in reqs]
    else:
        # Analysis is a single request/response per asset with no queue to poll, so the only ceiling
        # is politeness to the vendor — the same 8 the audio batch uses.
        with ThreadPoolExecutor(max_workers=min(8, len(reqs))) as ex:
            results = list(ex.map(_run, reqs))
    return supercmo_skills.batch_envelope(results, noun)


IMAGE_ANALYSIS = {
    "name": "image_analysis",
    "description": tool_specs.IMAGE_ANALYSIS_DESCRIPTION,
    "inputSchema": tool_specs.object_schema(
        tool_specs.IMAGE_ANALYSIS_PROPERTIES, tool_specs.IMAGE_ANALYSIS_REQUIRED),
}


def image_analysis(args):
    return _batch(args, "image", lambda r, dry: supercmo_skills.image_analysis(
        image=r.get("image"), prompt=r.get("prompt"), dry_run=dry), "image")


registry.register(IMAGE_ANALYSIS, image_analysis)


VIDEO_ANALYSIS = {
    "name": "video_analysis",
    "description": tool_specs.VIDEO_ANALYSIS_DESCRIPTION,
    "inputSchema": tool_specs.object_schema(
        tool_specs.VIDEO_ANALYSIS_PROPERTIES, tool_specs.VIDEO_ANALYSIS_REQUIRED),
}


def video_analysis(args):
    return _batch(args, "video", lambda r, dry: supercmo_skills.video_analysis(
        video=r.get("video"), prompt=r.get("prompt"), dry_run=dry), "video")


registry.register(VIDEO_ANALYSIS, video_analysis)
