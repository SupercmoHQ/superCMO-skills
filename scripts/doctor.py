#!/usr/bin/env python3
"""supercmo doctor — show which media-generation keys are set vs missing, what each enables,
and which capabilities are ready. With --check, do a FREE key-validity probe where a provider
implements one (never a paid generation).

  python3 scripts/doctor.py          # enumerate keys + per-capability readiness
  python3 scripts/doctor.py --check  # + free reachability probe

Agents get the same data host-agnostically via the `setup_status` MCP tool (no path needed).
Paste this output into a GitHub issue when reporting a skill problem.
"""
import os
import sys

_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from supercmo_skills import readiness  # noqa: E402


def main():
    check = "--check" in sys.argv[1:]
    st = readiness.status(check=check)
    print("SuperCMO doctor — media keys\n")
    print(f"  source: {st['source']}\n")

    for p in st["providers"]:
        mark = "✓" if p["set"] else "·"
        line = f"  {mark} {p['env_var']:<22} {'set' if p['set'] else 'missing':<8} {p['enables']}"
        if not p["set"]:
            line += f"   → get one at {p['signup']}"
        elif "probe" in p:
            line += f"   [{p['probe']}]"
        print(line)

    m = st["managed"]
    print(f"  {'✓' if m['set'] else '·'} {m['env_var']:<22} {'set' if m['set'] else 'missing':<8} {m['note']}")
    if not m["set"]:
        print(f"      → {m['setup']}")

    print("\n  capabilities ready with current keys:")
    for cap in ("image", "video", "audio"):
        s = st["capabilities"][cap]
        print(f"    {'✓' if s else '✗'} {cap:<6} ({s or 'no key'})")

    print(f"\n  {st['hint']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
