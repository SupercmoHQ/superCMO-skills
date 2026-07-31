#!/usr/bin/env python3
"""Listing gate — the money/social-safety check layered on top of quick_validate.py.

`quick_validate.py` owns structure + frontmatter. This adds, per skill under `skills/`:

  1. Scripts smoke — every `*.py` in the skill is syntactically valid (compile, no exec).
  2. Write-risk tag — read `metadata.writes` (spend | social | none; default none).
  3. spend/social only — the skill must expose a `--dry-run` entrypoint, and running it
     with `--dry-run` exits 0 offline. No test suite required, no live posting/spend.

Deliberately light: authoring is delegated; this just enforces the author contract so a
money/social skill can't ship without a safe dry-run path. Stdlib-only (matches CI).

    python3 scripts/listing_gate.py             # gate the repo (blocking)
    python3 scripts/listing_gate.py --selftest  # verify the gate logic itself
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WRITES_RE = re.compile(r"^\s*writes\s*:\s*[\"']?(?P<v>[a-zA-Z]+)", re.M)
VALID_WRITES = {"spend", "social", "none"}
DRY_RUN = "--dry-run"
RUN_TIMEOUT = 30
_OFFLINE_CLEAR = (
    "SUPERCMO_API_KEY", "SUPERCMO_API_URL", "FAL_KEY",
    "GEMINI_API_KEY", "ELEVENLABS_API_KEY", "FIRECRAWL_API_KEY",
)


def _frontmatter(skill_md: str) -> str:
    try:
        with open(skill_md, encoding="utf-8") as f:
            parts = f.read().split("---", 2)
        return parts[1] if len(parts) >= 3 else ""
    except Exception:
        return ""


def writes_tag(skill_md: str) -> str:
    """metadata.writes value; 'none' if absent; 'INVALID:<v>' for an unrecognized value."""
    m = WRITES_RE.search(_frontmatter(skill_md))
    if not m:
        return "none"
    v = m.group("v").lower()
    return v if v in VALID_WRITES else "INVALID:" + v


def _py_files(skill_dir: str) -> list[str]:
    out = []
    for root, _, files in os.walk(skill_dir):
        for fn in files:
            if fn.endswith(".py"):
                out.append(os.path.join(root, fn))
    return out


def _dry_run_scripts(skill_dir: str) -> list[str]:
    """*.py in the skill that declare a --dry-run flag."""
    found = []
    for p in _py_files(skill_dir):
        try:
            with open(p, encoding="utf-8") as f:
                if DRY_RUN in f.read():
                    found.append(p)
        except Exception:
            pass
    return found


def _run_dry(script: str) -> tuple[bool, str]:
    env = dict(os.environ)
    # offline; let scripts import the repo's stdlib helpers (supercmo_skills/supercmo_env live in scripts/)
    env["PYTHONPATH"] = os.pathsep.join(
        [os.path.join(REPO_ROOT, "scripts"), REPO_ROOT, env.get("PYTHONPATH", "")]
    )
    for k in _OFFLINE_CLEAR:
        env.pop(k, None)
    try:
        r = subprocess.run(
            [sys.executable, script, DRY_RUN], cwd=REPO_ROOT, env=env,
            capture_output=True, text=True, timeout=RUN_TIMEOUT,
        )
    except subprocess.TimeoutExpired:
        return False, f"--dry-run timed out (>{RUN_TIMEOUT}s)"
    if r.returncode != 0:
        return False, f"--dry-run exit {r.returncode}: {(r.stderr or r.stdout).strip()[:300]}"
    return True, ""


def gate_skill(skill_dir: str) -> list[str]:
    """Return a list of error strings for one skill ([] = passes)."""
    name = os.path.basename(skill_dir.rstrip("/"))
    skill_md = os.path.join(skill_dir, "SKILL.md")
    if not os.path.isfile(skill_md):
        return []  # quick_validate owns the missing-SKILL.md error
    errors = []

    # 1. scripts smoke — syntax only, no execution, no .pyc artifacts
    for p in _py_files(skill_dir):
        try:
            with open(p, encoding="utf-8") as f:
                compile(f.read(), p, "exec")
        except SyntaxError as e:
            errors.append(f"{name}: syntax error in {os.path.relpath(p, skill_dir)}: {e.msg} (line {e.lineno})")

    # 2. write-risk tag
    w = writes_tag(skill_md)
    if w.startswith("INVALID:"):
        errors.append(f"{name}: metadata.writes='{w.split(':', 1)[1]}' invalid (use spend|social|none)")
        return errors

    # 3. spend/social → must expose a --dry-run entrypoint that exits 0 offline
    if w in ("spend", "social"):
        scripts = _dry_run_scripts(skill_dir)
        if not scripts:
            errors.append(f"{name}: writes={w} skill must expose a --dry-run entrypoint (none found)")
        for s in scripts:
            ok, why = _run_dry(s)
            if not ok:
                errors.append(f"{name}: {os.path.relpath(s, skill_dir)} {why}")
    return errors


def gate_repo(repo_root: str = REPO_ROOT) -> bool:
    skills_dir = os.path.join(repo_root, "skills")
    if not os.path.isdir(skills_dir):
        print("❌ Listing gate: skills/ missing")
        return False
    all_errors = []
    for item in sorted(os.listdir(skills_dir)):
        d = os.path.join(skills_dir, item)
        if os.path.isdir(d):
            all_errors += gate_skill(d)
    if all_errors:
        print("❌ Listing gate FAILED:")
        for e in all_errors:
            print(f"  - {e}")
        return False
    print("✓ Listing gate PASSED (scripts compile; spend/social skills have a working --dry-run).")
    return True


def selftest() -> bool:
    """Build throwaway skills and assert the gate's verdicts."""
    import shutil
    import tempfile

    tmp = tempfile.mkdtemp(prefix="listing_gate_selftest_")
    good = "import sys\nif '--dry-run' in sys.argv:\n    print('dry ok'); sys.exit(0)\nsys.exit(1)\n"
    dryfail = "import sys\nif '--dry-run' in sys.argv:\n    sys.exit(3)\nsys.exit(0)\n"
    nodry = "print('no dry-run flag here')\n"
    broken = "def (:\n"

    def mk(name, writes, body=None):
        d = os.path.join(tmp, "skills", name)
        os.makedirs(os.path.join(d, "scripts"), exist_ok=True)
        meta = f"\nmetadata:\n  writes: {writes}\n" if writes else "\n"
        with open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8") as f:
            f.write(f"---\nname: {name}\ndescription: test{meta}---\n# {name}\n")
        if body is not None:
            with open(os.path.join(d, "scripts", "run.py"), "w", encoding="utf-8") as f:
                f.write(body)
        return d

    cases = [
        ("media-none", mk("media-none", "none"), True),               # no scripts, none → pass
        ("none-with-script", mk("none-x", "none", nodry), True),      # none never needs --dry-run
        ("spend-good", mk("spend-good", "spend", good), True),        # spend + --dry-run exit 0 → pass
        ("spend-nodry", mk("spend-nodry", "spend", nodry), False),   # spend, no --dry-run → fail
        ("spend-dryfail", mk("spend-dryfail", "spend", dryfail), False),  # --dry-run exit 3 → fail
        ("social-good", mk("social-good", "social", good), True),     # social + --dry-run exit 0 → pass
        ("syntax", mk("syntax", "none", broken), False),             # compile fails → fail
        ("badtag", mk("badtag", "spendy"), False),                   # invalid writes value → fail
    ]
    ok = True
    try:
        for label, d, want_pass in cases:
            errs = gate_skill(d)
            got_pass = not errs
            mark = "ok " if got_pass == want_pass else "FAIL"
            if got_pass != want_pass:
                ok = False
            print(f"  [{mark}] {label}: pass={got_pass} (want {want_pass}){' ' + str(errs) if errs else ''}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("✓ selftest PASSED" if ok else "❌ selftest FAILED")
    return ok


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if selftest() else 1)
    sys.exit(0 if gate_repo() else 1)
