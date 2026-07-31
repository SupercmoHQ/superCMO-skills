"""Audio generation tools — thin MCP binding over supercmo_skills.

All catalog + routing + vendor logic lives in supercmo_skills; the schema lives once in tool_specs.
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


AUDIO_GENERATE = {
    "name": "audio_generate",
    "description": tool_specs.AUDIO_GENERATE_DESCRIPTION,
    "inputSchema": tool_specs.object_schema(
        tool_specs.AUDIO_GENERATE_PROPERTIES, tool_specs.AUDIO_GENERATE_REQUIRED),
}


def audio_generate(args):
    reqs = args.get("requests")
    dry_run = bool(args.get("dry_run", False))
    if not isinstance(reqs, list) or not reqs:
        return {"ok": False, "error": "requests must be a non-empty list of audio request objects (1-10)."}
    if len(reqs) > 10:
        return {"ok": False, "error": f"at most 10 requests per call; got {len(reqs)}.",
                "hint": "split into more calls"}

    def _one(r):
        if not isinstance(r, dict) or not r.get("text"):
            return {"ok": False, "error": "each request must be an object with the text to speak."}
        knobs = {}
        for k in ("speed", "stability", "style", "similarity_boost"):
            if r.get(k) is None:
                continue
            try:
                knobs[k] = float(r[k])
            except (TypeError, ValueError):
                return {"ok": False, "error": f"{k} must be a number; got {r[k]!r}."}
        return supercmo_skills.audio_generate(
            text=r.get("text"), type=r.get("type") or "speech", model=r.get("model"),
            voice=r.get("voice"), format=r.get("format"), dry_run=dry_run, **knobs)

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


registry.register(AUDIO_GENERATE, audio_generate)


LIST_AUDIO_MODELS = {
    "name": "list_audio_models",
    "description": tool_specs.LIST_AUDIO_MODELS_DESCRIPTION,
    "inputSchema": tool_specs.object_schema(
        tool_specs.LIST_AUDIO_MODELS_PROPERTIES, tool_specs.LIST_AUDIO_MODELS_REQUIRED),
}


def list_audio_models(args):
    return catalog.audio_models_listing(args.get("query"))


registry.register(LIST_AUDIO_MODELS, list_audio_models)


LIST_VOICES = {
    "name": "list_voices",
    "description": tool_specs.LIST_VOICES_DESCRIPTION,
    "inputSchema": tool_specs.object_schema(
        tool_specs.LIST_VOICES_PROPERTIES, tool_specs.LIST_VOICES_REQUIRED),
}


def list_voices(args):
    return supercmo_skills.list_voices(
        search=args.get("search"), gender=args.get("gender"), accent=args.get("accent"),
        age=args.get("age"), use_case=args.get("use_case"), language=args.get("language"),
        limit=int(args["limit"]) if args.get("limit") is not None else 8)


registry.register(LIST_VOICES, list_voices)
