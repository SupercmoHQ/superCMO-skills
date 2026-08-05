"""Self-check: `python -m supercmo_skills` — asserts the gateway resolver routes correctly.

The smallest thing that fails if routing breaks. No network (dry_run).
"""
import os

import supercmo_env
import supercmo_skills as core


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
        for key in (
            "FAL_KEY", "GEMINI_API_KEY", "ELEVENLABS_API_KEY", "FIRECRAWL_API_KEY",
            "SUPERCMO_API_KEY",
        ):
            os.environ.pop(key, None)
        os.environ["SUPERCMO_API_KEY"] = "managed"
        seen = []
        real_proxy_request = supercmo_env.proxy_request
        supercmo_env.proxy_request = lambda capability, body, **kwargs: (
            seen.append((capability, kwargs.get("call_id")))
            or {"ok": False, "error": "test-stop"}
        )
        try:
            core.image_generate("x", model="nano-banana-2", wait=False)
            core.url_extraction("https://example.test")
            assert [capability for capability, _call_id in seen] == ["image", "extract"], seen
            call_ids = [call_id for _capability, call_id in seen]
            assert all(isinstance(call_id, str) and len(call_id) == 32 for call_id in call_ids), seen
            assert len(set(call_ids)) == len(call_ids), seen
        finally:
            supercmo_env.proxy_request = real_proxy_request
    finally:
        supercmo_env.reload_keys = real_reload_keys
    print("supercmo_skills self-check OK")


if __name__ == "__main__":
    main()
