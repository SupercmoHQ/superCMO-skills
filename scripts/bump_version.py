#!/usr/bin/env python3
"""Single-source the release version.

The canonical version lives in ONE place: package.json "version". This script
stamps that value into every other manifest + uvx pin, so a release bump is one
command instead of hand-editing ~16 spots. `--check` verifies nothing drifted
(release.yml calls it in CI, so the list of version-bearing files lives here and
nowhere else).

Usage:
  bump_version.py X.Y.Z            # set the version everywhere (package.json + all derived spots)
  bump_version.py --check          # verify every spot == package.json (exit 1 on drift)
  bump_version.py --check --tag vX.Y.Z   # also require package.json == the tag (release.yml)

To add a new version-bearing file: append it to FILES and it is covered by both
stamp and check automatically.
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANONICAL = "package.json"

# Every file that carries the version. Both plain version fields ("version": "X")
# and uvx pins (supercmo-skills@X) are stamped to the canonical value.
FILES = [
    "package.json",
    "pyproject.toml",
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    ".codex-plugin/plugin.json",
    ".codex-plugin/marketplace.json",
    ".codex-plugin/mcp.json",
    ".mcp.json",
    "server.json",
    "gemini-extension.json",
    "mcpb/manifest.json",
    "scripts/supercmo_skills/mcp/server.py",
]

_V = r"\d+\.\d+\.\d+(?:[-.+][0-9A-Za-z.]+)?"
# Each rule captures (prefix, version, suffix); only the version is replaced, so
# formatting is preserved byte-for-byte. Anchored to keys/prefixes so a schema
# version like mcpb "manifest_version": "0.3" is never touched.
RULES = [
    re.compile(r'("version":\s*")(' + _V + r')(")'),        # JSON version fields
    re.compile(r'(^version = ")(' + _V + r')(")', re.M),    # pyproject.toml
    re.compile(r'(SERVER_VERSION = ")(' + _V + r')(")'),    # server.py
    re.compile(r'(supercmo-skills@)(' + _V + r')()'),       # uvx pins (empty suffix group)
]


def _read(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as f:
        return f.read()


def canonical():
    return json.loads(_read(CANONICAL))["version"]


def stamp(new):
    for rel in FILES:
        text = _read(rel)
        for pat in RULES:
            text = pat.sub(lambda m: m.group(1) + new + m.group(3), text)
        with open(os.path.join(ROOT, rel), "w", encoding="utf-8") as f:
            f.write(text)


def drift(canon):
    """Return [(file, found_version), ...] for every spot that != canon."""
    bad = []
    for rel in FILES:
        text = _read(rel)
        for pat in RULES:
            for m in pat.finditer(text):
                if m.group(2) != canon:
                    bad.append((rel, m.group(2)))
    return bad


def main():
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)

    if args[0] == "--check":
        canon = canonical()
        tag = None
        if "--tag" in args:
            tag = args[args.index("--tag") + 1].lstrip("v")
        bad = drift(canon)
        for rel, v in bad:
            print(f"❌ {rel}: {v} != canonical {canon}")
        if tag and canon != tag:
            print(f"❌ tag {tag} != canonical {canon} (package.json)")
            bad.append(("tag", tag))
        if bad:
            sys.exit(1)
        print(f"✅ version in sync @ {canon}" + (" (== tag)" if tag else ""))
        return

    new = args[0].lstrip("v")
    if not re.fullmatch(_V, new):
        sys.exit(f"invalid version: {new!r}")
    stamp(new)
    missed = drift(new)
    if missed:
        for rel, v in missed:
            print(f"❌ {rel}: {v} (stamp missed a spot)")
        sys.exit(1)
    print(f"✅ stamped {new} across {len(FILES)} files")


if __name__ == "__main__":
    main()
