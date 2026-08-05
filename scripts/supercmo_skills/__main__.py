"""Self-check: `python -m supercmo_skills` — asserts the gateway resolver routes correctly.

The smallest thing that fails if routing breaks. No network (dry_run).
"""
import os

import supercmo_env
import supercmo_skills as core
from supercmo_skills import tool_specs


def _route_of(**env):
    for k in ("FAL_KEY", "SUPERCMO_API_KEY"):
        os.environ.pop(k, None)
    os.environ.update(env)
    r = core.image_generate("a red bicycle", model="nano-banana-2", dry_run=True)
    return r.get("route") or r.get("error")


def main():
    real_reload_keys = supercmo_env.reload_keys
    supercmo_env.reload_keys = lambda: None
    try:
        assert _route_of(FAL_KEY="x") == "fal", "BYO fal route should win"
        assert _route_of(SUPERCMO_API_KEY="x") == "proxy", "managed proxy when no BYO route available"
        assert _route_of(FAL_KEY="x", SUPERCMO_API_KEY="y") == "fal", "BYO-direct > managed"
        assert _route_of() == "no_provider_configured", "neither set -> actionable error"
        bad = core.image_generate("x", model="does-not-exist", dry_run=True)
        assert bad.get("error", "").startswith("unknown image model"), bad
        assert tool_specs.operation_call_id("one-operation", 2) == "one-operation:2"
        assert tool_specs.operation_call_id("") is None

        for key in ("FAL_KEY", "SUPERCMO_API_KEY"):
            os.environ.pop(key, None)
        os.environ["SUPERCMO_API_KEY"] = "managed"
        missing = core.image_generate("x", model="nano-banana-2", wait=False)
        assert missing.get("error") == "idempotency_key_required", missing
        seen = {}
        real_proxy_request = supercmo_env.proxy_request
        supercmo_env.proxy_request = lambda capability, body, **kwargs: (
            seen.update(capability=capability, call_id=kwargs.get("call_id"))
            or {"ok": False, "error": "test-stop"}
        )
        try:
            core.image_generate(
                "x", model="nano-banana-2", wait=False, call_id="one-operation:0"
            )
            assert seen == {"capability": "image", "call_id": "one-operation:0"}, seen
        finally:
            supercmo_env.proxy_request = real_proxy_request
    finally:
        supercmo_env.reload_keys = real_reload_keys
    print("supercmo_skills self-check OK")


if __name__ == "__main__":
    main()
