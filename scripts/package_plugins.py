#!/usr/bin/env python3
"""Package the repo-as-one-plugin into a distributable tarball.

Repo-as-one-plugin: the whole repo IS the plugin. Native install
(`/plugin marketplace add ...`) needs no compiler — this tarball exists only as
the additive delivery artifact for the hosted product (served from R2 / the
install endpoint). It bundles the plugin components, excluding dev-only files.
"""
import os
import sys
import json
import shutil
import tarfile

# Top-level entries that make up the installable plugin.
PLUGIN_ENTRIES = [".claude-plugin", "skills", "agents", "scripts", "opencode.json"]

# Dev-only / non-runtime files excluded from the shipped bundle.
EXCLUDE_PATTERNS = shutil.ignore_patterns(
    "evals", "__pycache__", "*.pyc", "*.pyo", "*.pyd",
    ".DS_Store", "node_modules", ".git", ".pytest_cache",
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

    staging = os.path.join("/tmp", "build", name)
    if os.path.exists(staging):
        shutil.rmtree(staging)
    os.makedirs(staging, exist_ok=True)

    for entry in PLUGIN_ENTRIES:
        src = os.path.join(repo_root, entry)
        if not os.path.exists(src):
            continue
        dest = os.path.join(staging, entry)
        if os.path.isdir(src):
            shutil.copytree(src, dest, ignore=EXCLUDE_PATTERNS)
        else:
            shutil.copy2(src, dest)

    dist_dir = os.path.join(repo_root, "dist")
    os.makedirs(dist_dir, exist_ok=True)
    tarball = os.path.join(dist_dir, f"{name}.tar.gz")
    with tarfile.open(tarball, "w:gz") as tar:
        for item in os.listdir(staging):
            tar.add(os.path.join(staging, item), arcname=item)

    shutil.rmtree(staging)
    print(f"✓ Packaged '{name}' → {tarball} ({os.path.getsize(tarball)} bytes).")
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
