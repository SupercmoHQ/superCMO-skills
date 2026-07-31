"""Job-status tool — thin MCP binding over supercmo_skills.

Rejoins a long-running generation submitted earlier (a `video_generate` result that came back
`{status:"pending", ...}`) and returns the finished media, or the same pending handle if it's still
running. All the submit/poll/rejoin logic lives in supercmo_skills; the schema lives once in tool_specs.
"""
import os
import sys
from concurrent.futures import ThreadPoolExecutor

PLUGIN_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(PLUGIN_ROOT, "scripts"))

import registry  # noqa: E402
import supercmo_skills  # noqa: E402
from supercmo_skills import tool_specs  # noqa: E402


JOB_STATUS = {
    "name": "job_status",
    "description": tool_specs.JOB_STATUS_DESCRIPTION,
    "inputSchema": tool_specs.object_schema(
        tool_specs.JOB_STATUS_PROPERTIES, tool_specs.JOB_STATUS_REQUIRED),
}


def job_status(args):
    jobs = args.get("jobs")
    if isinstance(jobs, dict):          # tolerate a single handle passed unwrapped
        jobs = [jobs]
    if not isinstance(jobs, list) or not jobs:
        return {"ok": False, "error": "jobs must be a non-empty list of pending job handle objects."}
    if len(jobs) > 10:
        return {"ok": False, "error": f"at most 10 jobs per call; got {len(jobs)}."}

    if len(jobs) == 1:
        results = [supercmo_skills.job_status(jobs[0])]
    else:                                # rejoin a batch concurrently
        with ThreadPoolExecutor(max_workers=min(8, len(jobs))) as ex:
            results = list(ex.map(supercmo_skills.job_status, jobs))
    pending = sum(1 for r in results if supercmo_skills.is_pending(r))
    out = {"ok": all(supercmo_skills.job_ok(x) for x in results), "count": len(results), "results": results}
    if pending:
        out["pending"] = pending
        out["hint"] = "still generating — call job_status again with each pending handle after a short wait (do not re-submit)."
    return out


registry.register(JOB_STATUS, job_status)
