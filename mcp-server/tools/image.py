"""Image generation tools — thin MCP binding over supercmo_skills.

All catalog + routing + vendor logic lives in supercmo_skills; this only declares the
schema and forwards the call.
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


IMAGE_GENERATE = {
    "name": "image_generate",
    "description": tool_specs.IMAGE_GENERATE_DESCRIPTION,
    "inputSchema": tool_specs.object_schema(
        tool_specs.IMAGE_GENERATE_PROPERTIES, tool_specs.IMAGE_GENERATE_REQUIRED),
}


def image_generate(args):
    reqs = args.get("requests")
    dry_run = bool(args.get("dry_run", False))
    if not isinstance(reqs, list) or not reqs:
        return {"ok": False, "error": "requests must be a non-empty list of image request objects (1-10)."}
    if len(reqs) > 10:
        return {"ok": False, "error": f"at most 10 requests per call; got {len(reqs)}.",
                "hint": "split into more calls"}
    def _one(r):
        if not isinstance(r, dict) or not r.get("prompt"):
            return {"ok": False, "error": "each request must be an object with a prompt."}
        return supercmo_skills.image_generate(
            prompt=r.get("prompt"), model=r.get("model"), aspect_ratio=r.get("aspect_ratio"),
            resolution=r.get("resolution"), reference_images=r.get("reference_images"), dry_run=dry_run)

    if dry_run or len(reqs) == 1:
        results = [_one(r) for r in reqs]
    else:                                     # multiple images → generate them in parallel
        with ThreadPoolExecutor(max_workers=min(8, len(reqs))) as ex:
            results = list(ex.map(_one, reqs))
    pending = sum(1 for r in results if supercmo_skills.is_pending(r))
    out = {"ok": all(supercmo_skills.job_ok(x) for x in results), "count": len(results), "results": results}
    if pending:
        out["pending"] = pending
        out["hint"] = "some images are still generating — call job_status with each pending image's job handle to retrieve it (do not re-submit)."
    return out


registry.register(IMAGE_GENERATE, image_generate)


LIST_IMAGE_MODELS = {
    "name": "list_image_models",
    "description": tool_specs.LIST_IMAGE_MODELS_DESCRIPTION,
    "inputSchema": tool_specs.object_schema(
        tool_specs.LIST_IMAGE_MODELS_PROPERTIES, tool_specs.LIST_IMAGE_MODELS_REQUIRED),
}


def list_image_models(args):
    return catalog.image_models_listing(args.get("query"))


registry.register(LIST_IMAGE_MODELS, list_image_models)
