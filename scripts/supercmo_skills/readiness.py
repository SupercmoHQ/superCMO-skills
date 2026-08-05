"""Setup readiness — the single function behind `scripts/doctor.py` (CLI) and the `setup_status`
MCP tool. It reports which media keys are configured and which capabilities are ready, deriving
everything from the one provider registry (`client.provider_modules()` + each provider's `BYOK_ENV`
/ `KEY_ENABLES` / `KEY_SIGNUP` / optional `probe`) so nothing is re-typed. No network unless
`check=True`, and even then only through the provider's own `probe()` (which brokers via
supercmo_env) — never raw HTTP here.
"""
import os

import supercmo_env

from . import catalog, client


def _capability_status(cap, managed):
    """One of "managed" | "BYO key" | None — is this capability generatable with the current keys?"""
    if managed:
        return "managed"
    # ready if ANY model in the capability resolves to a direct (BYO-keyed) route
    for row in catalog.list_models(cap):
        if client.select_route(cap, row["model"], allow_proxy=False)[0] == "direct":
            return "BYO key"
    return None


def status(check=False):
    """Structured setup status. `check=True` adds a FREE key-validity probe where a provider
    implements one (never a paid generation)."""
    supercmo_env.reload_keys()  # re-read ~/.supercmo/.env so a just-added key shows live (no restart)
    providers = []
    for mod in client.provider_modules().values():
        env_var = mod.BYOK_ENV
        row = {
            "env_var": env_var,
            "set": bool(os.environ.get(env_var)),
            "enables": getattr(mod, "KEY_ENABLES", ""),
            "signup": getattr(mod, "KEY_SIGNUP", ""),
        }
        probe = getattr(mod, "probe", None)
        if check and row["set"] and callable(probe):
            row["probe"] = probe()
        providers.append(row)

    managed = bool(supercmo_env.supercmo_key())
    capabilities = {c: _capability_status(c, managed) for c in ("image", "video", "audio")}
    configured = managed or any(p["set"] for p in providers)

    return {
        "ok": True,
        "source": "~/.supercmo/.env (re-read live on each call), or a shell export",
        "providers": providers,
        "managed": {
            "env_var": "SUPERCMO_API_KEY",
            "set": managed,
            "setup": "run `npx --yes github:SupercmoHQ/superCMO-skills login` (opens getsupercmo.ai to sign in + authorize; writes the key)",
            "note": "managed metered proxy — generate on SuperCMO's keys, pay per use (optional; BYOK needs no key)",
        },
        "capabilities": capabilities,
        "configured": configured,
        "hint": (
            "No key set. Two options: (A) Managed — run "
            "`npx --yes github:SupercmoHQ/superCMO-skills login` to sign in and pay per use; or "
            "(B) bring your own keys (free) — add a vendor key to ~/.supercmo/.env "
            "(e.g. FAL_KEY=your-key). Let the user pick; don't run login unless they choose managed. Then retry."
            if not configured
            else "FAL_KEY covers image + video; ELEVENLABS_API_KEY covers speech."
        ),
    }


if __name__ == "__main__":
    # ponytail: env-driven self-check — no key set, then FAL_KEY set.
    os.environ.pop("SUPERCMO_API_KEY", None)
    for v in (m.BYOK_ENV for m in client.provider_modules().values()):
        os.environ.pop(v, None)
    st = status()
    assert st["configured"] is False and all(v is None for v in st["capabilities"].values())
    assert {p["env_var"] for p in st["providers"]} == {m.BYOK_ENV for m in client.provider_modules().values()}
    os.environ["FAL_KEY"] = "x"
    st = status()
    assert st["configured"] is True and st["capabilities"]["image"] == "BYO key"
    del os.environ["FAL_KEY"]
    print("readiness OK")
