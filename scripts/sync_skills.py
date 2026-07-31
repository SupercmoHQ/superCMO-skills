#!/usr/bin/env python3
"""Regenerate the README skills catalog from skills/*/SKILL.md frontmatter.

The table between `<!-- SKILLS:START -->` and `<!-- SKILLS:END -->` in README.md is
AUTO-GENERATED — never hand-edit it. Run this after adding/renaming/removing a skill;
CI (`--check`) fails if it drifts. A skill opts out of the catalog with
`metadata.catalog: false` (e.g. the authoring template).

Each row's blurb is the skill's hand-written `metadata.summary` (a human-facing catalog
line, shown verbatim), falling back to the agent-facing `description` (truncated) if
no summary is set.

  usage: python3 scripts/sync_skills.py [--check]
  exit:  0 = written / already in sync · 1 = out of date (--check) or error
"""
import argparse
import glob
import os
import re
import sys

try:
    import yaml
except ImportError:
    sys.exit("sync_skills requires PyYAML — run: pip install pyyaml")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
README = os.path.join(REPO, "README.md")
MARKERS = re.compile(r"(<!-- SKILLS:START[^\n]*-->\n)[\s\S]*?(\n<!-- SKILLS:END -->)")


def frontmatter(path):
    txt = open(path, encoding="utf-8").read()
    m = re.match(r"^---\n(.*?)\n---", txt, re.S)
    return (yaml.safe_load(m.group(1)) or {}) if m else {}


def blurb(fm, maxlen=120):
    # Prefer the hand-written, human-facing `metadata.summary` (shown verbatim — it's written for
    # this catalog); fall back to the agent-facing `description`, truncated at a word boundary.
    summary = str((fm.get("metadata") or {}).get("summary") or "").strip()
    if summary:
        return summary
    s = str(fm.get("description") or "").strip()
    if len(s) <= maxlen:
        return s
    return s[:maxlen].rsplit(" ", 1)[0] + "…"


def catalog_skills():
    rows = []
    for d in sorted(glob.glob(os.path.join(REPO, "skills", "*"))):
        f = os.path.join(d, "SKILL.md")
        if not os.path.isfile(f):
            continue
        fm = frontmatter(f)
        if (fm.get("metadata") or {}).get("catalog") is False:  # opt-out (template)
            continue
        rows.append((fm.get("name") or os.path.basename(d), os.path.basename(d), blurb(fm)))
    return sorted(rows)


def render(rows):
    head = "| Skill | Description |\n|-------|-------------|"
    body = "\n".join(f"| [{name}](skills/{d}/) | {b} |" for name, d, b in rows)
    return head + "\n" + body


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="fail if README is out of date (CI)")
    args = ap.parse_args()

    content = open(README, encoding="utf-8").read()
    if not MARKERS.search(content):
        sys.exit("no <!-- SKILLS:START/END --> markers in README.md")

    rows = catalog_skills()
    new = MARKERS.sub(lambda m: m.group(1) + render(rows) + m.group(2), content)

    if new == content:
        print(f"README skills table already in sync ({len(rows)} skills)")
        return
    if args.check:
        sys.exit("README skills table is OUT OF DATE — run: python3 scripts/sync_skills.py")
    open(README, "w", encoding="utf-8").write(new)
    print(f"Updated README skills table ({len(rows)} skills)")


if __name__ == "__main__":
    main()
