#!/usr/bin/env python3
"""supercmo doctor — show which media-generation keys are set vs missing, what each enables,
and which capabilities are ready. With --check, do a FREE key-validity probe where one exists
(never a paid generation).

  python3 scripts/doctor.py          # enumerate keys + per-capability readiness
  python3 scripts/doctor.py --check  # + free reachability probe (OpenAI / xAI list-models)

Paste the output into a GitHub issue when reporting a skill problem.
"""
import os
import sys

_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import supercmo_env  # noqa: E402
from supercmo_skills import catalog, client  # noqa: E402

# BYO vendor keys the media client routes over + what each unlocks.
VENDORS = [
    ("FAL_KEY", "fal.ai", "image · video · tts  (broadest — recommended starter)"),
    ("OPENAI_API_KEY", "platform.openai.com", "image (gpt-image) · tts"),
    ("GEMINI_API_KEY", "aistudio.google.com", "tts · image analysis (vision)"),
    ("XAI_API_KEY", "x.ai", "image · video (grok)"),
    ("ELEVENLABS_API_KEY", "elevenlabs.io", "tts (expressive voices)"),
    ("FIRECRAWL_API_KEY", "firecrawl.dev", "url extraction (product / web pages)"),
]

# Vendors with a FREE list-models endpoint we can use to validate a key (no paid call).
_PROBE = {
    "OPENAI_API_KEY": "https://api.openai.com/v1/models",
    "XAI_API_KEY": "https://api.x.ai/v1/models",
}


def _probe(env_var):
    parsed, status, _err = supercmo_env._request(
        "GET", _PROBE[env_var], headers={"Authorization": f"Bearer {os.environ.get(env_var)}"})
    return "reachable" if parsed is not None else f"unreachable (HTTP {status})"


def main():
    check = "--check" in sys.argv[1:]
    print("SuperCMO doctor — media keys\n")
    print("  source: process environment (set keys in your host's MCP config `env` block, "
          "or export them in your shell)\n")

    for env_var, where, enables in VENDORS:
        is_set = bool(os.environ.get(env_var))
        line = f"  {'✓' if is_set else '·'} {env_var:<22} {'set' if is_set else 'missing':<8} {enables}"
        if not is_set:
            line += f"   → get one at {where}"
        elif check and env_var in _PROBE:
            line += f"   [{_probe(env_var)}]"
        print(line)

    managed = bool(supercmo_env.supercmo_key())
    print(f"  {'✓' if managed else '·'} {'SUPERCMO_API_KEY':<22} {'set' if managed else 'missing':<8} "
          "managed metered proxy (optional; BYOK needs no key)")
    if not managed:
        print("      → managed key: buy credits + mint at getsupercmo.ai/settings?tab=keys")

    print("\n  capabilities ready with current keys:")
    for cap in ("image", "video", "tts"):
        if managed:
            status = "managed"
        else:  # ready if ANY model in the capability has an available BYO route
            status = next(("BYO key" for row in catalog.list_models(cap)
                           if client.select_route(cap, row["model"], allow_proxy=False)[0] == "direct"), None)
        print(f"    {'✓' if status else '✗'} {cap:<6} ({status or 'no key'})")

    if not any(os.environ.get(v) for v, _, _ in VENDORS) and not managed:
        print("\n  No keys yet. Add one to your host's MCP config `env` block (e.g. FAL_KEY=...) "
              "or export it in your shell, then re-run.")
    else:
        print("\n  Tip: FAL_KEY alone covers image + video + tts.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
