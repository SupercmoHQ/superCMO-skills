"""Self-check: `python -m supercmo_skills` — asserts the gateway resolver routes correctly.

ponytail: the smallest thing that fails if routing breaks. No network (dry_run).
"""
import os

import supercmo_skills as core


def _route_of(**env):
    for k in ("FAL_KEY", "SUPERCMO_API_KEY"):
        os.environ.pop(k, None)
    os.environ.update(env)
    r = core.image_generate("a red bicycle", model="nano-banana-2", dry_run=True)
    return r.get("route") or r.get("error")


def main():
    assert _route_of(FAL_KEY="x") == "fal", "BYO fal route should win"
    assert _route_of(SUPERCMO_API_KEY="x") == "proxy", "managed proxy when no BYO route available"
    assert _route_of(FAL_KEY="x", SUPERCMO_API_KEY="y") == "fal", "BYO-direct > managed"
    assert _route_of() == "no_provider_configured", "neither set -> actionable error"
    bad = core.image_generate("x", model="does-not-exist", dry_run=True)
    assert bad.get("error", "").startswith("unknown image model"), bad
    print("supercmo_skills self-check OK")


if __name__ == "__main__":
    main()
