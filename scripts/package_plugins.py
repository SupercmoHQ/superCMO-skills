#!/usr/bin/env python3
"""Package the repo-as-one-plugin into a distributable plugin bundle.

Repo-as-one-plugin: the whole repo IS the plugin. Native install
(`/plugin marketplace add ...`) needs no compiler — this bundle is the additive
delivery artifact: what a user uploads via Claude Cowork / desktop
("Settings -> Plugins -> Upload local plugin", a `.zip`), and what `release.yml`
attaches to each GitHub Release.

It bundles every runtime plugin component and excludes dev-only files. It also
excludes the top-level `bin/` (the npx installer) and `package.json`:
claude.ai-hosted plugins forbid a top-level `bin/` (executables on PATH with no
approval surface), so the uploaded bundle must not contain it.
"""
import os
import sys
import json
import shutil
import zipfile
import tempfile

# Top-level entries that make up the installable plugin — everything the plugin
# needs at runtime, and NOT bin/ or package.json (see the module docstring).
PLUGIN_ENTRIES = [
    ".claude-plugin",   # plugin.json / marketplace.json / supercmo.json
    ".mcp.json",        # declares the supercmo MCP server (points at mcp-server/)
    "mcp-server",       # the MCP server the skills call
    "skills",           # the skills
    "scripts",          # the engine the MCP server imports (supercmo_skills, etc.)
    "LICENSE",          # Apache-2.0 (redistribution)
    "NOTICE",           # Apache-2.0 NOTICE (redistribution)
]

# Dev-only / non-runtime files excluded from the shipped bundle.
EXCLUDE_PATTERNS = shutil.ignore_patterns(
    "evals", "__pycache__", "*.pyc", "*.pyo", "*.pyd", "*.egg-info",
    ".DS_Store", "node_modules", ".git", ".pytest_cache", ".benchmarks",
)


def plugin_name(repo_root):
    """Read the plugin name from the root plugin.json (fallback: 'supercmo')."""
    try:
        with open(os.path.join(repo_root, ".claude-plugin", "plugin.json"), encoding="utf-8") as f:
            return json.load(f).get("name", "supercmo")
    except Exception:
        return "supercmo"


def package(repo_root):
    name = plugin_name(repo_root)
    print(f"--> Packaging repo-as-one-plugin: {name}")

    dist_dir = os.path.join(repo_root, "dist")
    os.makedirs(dist_dir, exist_ok=True)
    bundle = os.path.join(dist_dir, f"{name}-plugin.zip")
    if os.path.exists(bundle):
        os.remove(bundle)

    with tempfile.TemporaryDirectory() as staging:
        for entry in PLUGIN_ENTRIES:
            src = os.path.join(repo_root, entry)
            if not os.path.exists(src):
                print(f"⚠️  missing plugin entry (skipped): {entry}")
                continue
            dest = os.path.join(staging, entry)
            if os.path.isdir(src):
                shutil.copytree(src, dest, ignore=EXCLUDE_PATTERNS)
            else:
                shutil.copy2(src, dest)

        with zipfile.ZipFile(bundle, "w", zipfile.ZIP_DEFLATED) as zf:
            for root, _dirs, files in os.walk(staging):
                for fn in sorted(files):
                    full = os.path.join(root, fn)
                    zf.write(full, arcname=os.path.relpath(full, staging))

    print(f"✓ Packaged '{name}' → {bundle} ({os.path.getsize(bundle)} bytes).")
    return True


def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.append(os.path.join(repo_root, "scripts"))
    import quick_validate
    print("=== Pre-package validation ===")
    if not (quick_validate.validate_skills(repo_root) and quick_validate.validate_plugin(repo_root)):
        print("❌ Validation failed. Aborting.")
        sys.exit(1)
    if not package(repo_root):
        sys.exit(1)
    print("\n✓ Package complete.")
    sys.exit(0)


if __name__ == "__main__":
    main()
