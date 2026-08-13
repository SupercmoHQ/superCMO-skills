#!/usr/bin/env python3
"""Structural + frontmatter validation for the repo-as-one-plugin layout.

The whole repo is a single Claude Code plugin: the root .claude-plugin/ holds the
manifests, and skills/ + agents/ at the root are the plugin's components (so a
native `/plugin marketplace add` installs working skills — no compiler required).

This is the blocking local/CI gate. The Agent Skills spec validator (`skills-ref`)
runs as an additional CI step (see .github/workflows/validate.yml).
"""
import os
import re
import sys
import json

try:
    import yaml
except ImportError:
    sys.exit("quick_validate requires PyYAML — run: pip install pyyaml")

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
RESERVED = ("claude", "anthropic")


def read_frontmatter(file_path):
    """Return (raw_frontmatter_text, parsed_dict) or (None, None).

    Parses with a STRICT YAML loader — the same parse strict hosts do (e.g. Cursor's plugin
    import). Frontmatter that only survives Claude Code's lenient parser (a stray `: `
    colon-space in a value, a tab, an unclosed quote) fails HERE, not silently in production.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        parts = content.split("---", 2)
        if len(parts) < 3:
            return None, None
        raw = parts[1]
        try:
            fm = yaml.safe_load(raw)
        except yaml.YAMLError as e:
            print(f"   (strict YAML: {str(e).splitlines()[0]})")
            return None, None
        if not isinstance(fm, dict):
            print("   (frontmatter is not a key: value mapping)")
            return None, None
        return raw, fm
    except Exception as e:
        print(f"Error parsing frontmatter for {file_path}: {e}")
        return None, None


def lint_frontmatter(raw, fm, folder):
    """Enforce §5 (schema) + §6 (naming). Returns a list of error strings."""
    errors = []

    name = fm.get("name", "")
    if not name:
        errors.append("missing 'name'")
    else:
        if name != folder:
            errors.append(f"name '{name}' != folder name '{folder}'")
        if len(name) > 64:
            errors.append("name exceeds 64 chars")
        if not NAME_RE.match(name):
            errors.append("name must match ^[a-z0-9]+(-[a-z0-9]+)*$")
        if any(w in name for w in RESERVED):
            errors.append("name contains a reserved word (claude/anthropic)")

    desc = fm.get("description", "")
    if not desc:
        errors.append("missing 'description'")
    elif len(desc) > 1024:
        errors.append("description exceeds 1024 chars")

    if "<" in raw or ">" in raw:
        errors.append("frontmatter must not contain '<' or '>' (no XML tags / injection guard)")

    for line in raw.splitlines():
        if re.match(r"^platforms\s*:", line):
            errors.append("forbidden field 'platforms' (not an Agent Skills field)")
        if re.match(r"^version\s*:", line):
            errors.append("top-level 'version' — put version under metadata")
        if re.match(r"^allowed-tools\s*:", line) and "[" in line:
            errors.append("malformed 'allowed-tools' — use space-separated patterns, not a JSON array")

    return errors


def validate_skills(repo_root):
    """Validate + lint every skill folder under skills/."""
    print("--> Validating skills registry...")
    skills_dir = os.path.join(repo_root, "skills")
    if not os.path.exists(skills_dir):
        print("❌ Error: skills/ directory is missing")
        return False

    valid = True
    for item in sorted(os.listdir(skills_dir)):
        skill_path = os.path.join(skills_dir, item)
        if not os.path.isdir(skill_path):
            continue
        skill_md = os.path.join(skill_path, "SKILL.md")
        if not os.path.exists(skill_md):
            print(f"❌ Error: Skill '{item}' is missing SKILL.md")
            valid = False
            continue
        raw, fm = read_frontmatter(skill_md)
        if raw is None:
            print(f"❌ Error: Skill '{item}' has invalid YAML frontmatter")
            valid = False
            continue
        for err in lint_frontmatter(raw, fm, item):
            print(f"❌ Error: Skill '{item}': {err}")
            valid = False

    if valid:
        print("✓ All skills pass structural + frontmatter lint.")
    return valid


def validate_agents(repo_root):
    """Lint top-level agents/*.md frontmatter (subagents). Bundled role prompts under a skill's
    own agents/ folder are intentionally frontmatter-free and are NOT checked here."""
    agents_dir = os.path.join(repo_root, "agents")
    if not os.path.isdir(agents_dir):
        return True
    print("--> Validating agents...")
    valid = True
    for fn in sorted(os.listdir(agents_dir)):
        if not fn.endswith(".md"):
            continue
        base = fn[:-3]
        raw, fm = read_frontmatter(os.path.join(agents_dir, fn))
        if raw is None:
            print(f"❌ Error: Agent '{fn}' has no/invalid YAML frontmatter (name + description required)")
            valid = False
            continue
        if fm.get("name", "") != base:
            print(f"❌ Error: Agent '{fn}': name '{fm.get('name', '')}' != file basename '{base}'")
            valid = False
        if not fm.get("description"):
            print(f"❌ Error: Agent '{fn}': missing 'description' (when-to-delegate)")
            valid = False
        if "<" in raw or ">" in raw:
            print(f"❌ Error: Agent '{fn}': frontmatter must not contain '<' or '>'")
            valid = False
    if valid:
        print("✓ All agents pass frontmatter lint.")
    return valid


def validate_plugin(repo_root):
    """Validate the root plugin manifests (repo-as-one-plugin)."""
    print("--> Validating root plugin manifests...")
    valid = True

    plugin_json = os.path.join(repo_root, ".claude-plugin", "plugin.json")
    if not os.path.exists(plugin_json):
        print("❌ Error: missing .claude-plugin/plugin.json")
        return False
    try:
        with open(plugin_json, "r", encoding="utf-8") as f:
            json.load(f)
    except Exception as e:
        print(f"❌ Error: invalid plugin.json: {e}")
        valid = False

    # SuperCMO hosted-product manifest — its OWN host dir, like .claude-plugin /
    # .codex-plugin. It is not a Claude file and must not sit in Claude's dir.
    supercmo_json = os.path.join(repo_root, ".supercmo-plugin", "supercmo.json")
    if os.path.exists(supercmo_json):
        try:
            with open(supercmo_json, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except Exception as e:
            print(f"❌ Error: invalid supercmo.json: {e}")
            return False
        for skill_name in manifest.get("skills", []):
            if not os.path.exists(os.path.join(repo_root, "skills", skill_name)):
                print(f"❌ Error: supercmo.json references missing skill: '{skill_name}'")
                valid = False
        for agent_file in manifest.get("agents", []):
            if not os.path.exists(os.path.join(repo_root, "agents", agent_file)):
                print(f"❌ Error: supercmo.json references missing agent: '{agent_file}'")
                valid = False
        for script_file in manifest.get("scripts", []):
            if not os.path.exists(os.path.join(repo_root, "scripts", script_file)):
                print(f"❌ Error: supercmo.json references missing script: '{script_file}'")
                valid = False

    if valid:
        print("✓ Root plugin manifests are valid.")
    return valid


def validate_marketplace(repo_root):
    """Validate the root marketplace.json."""
    print("--> Validating root marketplace manifest...")
    market_json = os.path.join(repo_root, ".claude-plugin", "marketplace.json")
    if not os.path.exists(market_json):
        print("❌ Error: missing .claude-plugin/marketplace.json")
        return False
    try:
        with open(market_json, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error: marketplace.json invalid JSON: {e}")
        return False

    valid = True
    if not data.get("name"):
        print("❌ Error: marketplace.json missing 'name'")
        valid = False
    if not isinstance(data.get("plugins"), list) or not data["plugins"]:
        print("❌ Error: marketplace.json missing 'plugins' list")
        valid = False
    else:
        for idx, plugin in enumerate(data["plugins"]):
            if not plugin.get("name"):
                print(f"❌ Error: marketplace plugin at index {idx} missing 'name'")
                valid = False
            src = plugin.get("source")
            if not src:
                print(f"❌ Error: marketplace plugin at index {idx} missing 'source'")
                valid = False
            elif not os.path.exists(os.path.normpath(os.path.join(repo_root, src))):
                print(f"❌ Error: marketplace plugin '{plugin.get('name')}' source missing: {src}")
                valid = False

    if valid:
        print("✓ Root marketplace manifest is valid.")
    return valid


def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print(f"=== Running Structural Validation on Repo: {repo_root} ===")

    ok = all([
        validate_skills(repo_root),
        validate_agents(repo_root),
        validate_plugin(repo_root),
        validate_marketplace(repo_root),
    ])

    if not ok:
        print("❌ Validation FAILED!")
        sys.exit(1)
    print("✓ Validation PASSED!")
    sys.exit(0)


if __name__ == "__main__":
    main()
