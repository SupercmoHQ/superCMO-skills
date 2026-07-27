#!/usr/bin/env python3
"""Extension gate — validates the NON-skill intern surfaces the other gates don't cover:
`optional-mcps/<name>/manifest.yaml` (connector catalog) and `hermes-plugins/<name>/` (plugins).

Why this exists: Hermes's `list_catalog()` SKIPS an invalid manifest SILENTLY, so a typo'd
connector would pass CI, ship to users, and simply never appear in `supercmo connect` with no
error anywhere. This gate makes that failure happen at PR time instead. It mirrors the fields
Hermes's `_parse_manifest` requires (a rejected/missing field there = a skipped entry) plus the
SuperCMO-only `category:` tag the approvals gate depends on.

Fails (exit 1) on:
  MCP manifests — bad/missing manifest_version, name (regex + == folder), description, transport
    (type + the type's required command/url), auth.type, api_key with no credentials, malformed
    category / tools.default_enabled / install(git+ref).
  Plugins — a hermes-plugins/<name>/ missing plugin.yaml or __init__.py, or whose __init__.py
    defines no `register` hook.

Needs PyYAML (the manifests are YAML); CI installs it. Run locally with `python3
scripts/check_extensions.py`; verify the gate logic itself with `--selftest`.
"""
import ast
import os
import re
import sys

try:
    import yaml
except ImportError:
    print("check_extensions: PyYAML is required — `pip install pyyaml` and re-run.", file=sys.stderr)
    sys.exit(1)

NAME_RE = re.compile(r"^[A-Za-z0-9_-]+$")  # Hermes mcp_catalog name rule
_CATEGORY_PAUSE = {"spend", "budget", "publish"}  # the tags the approvals gate acts on (advisory here)


def _err(errors, where, msg):
    errors.append(f"{where}: {msg}")


def check_mcp_manifests(repo_root):
    """Validate every optional-mcps/<name>/manifest.yaml. Returns a list of error strings."""
    errors = []
    root = os.path.join(repo_root, "optional-mcps")
    if not os.path.isdir(root):
        return errors  # nothing to validate
    for name in sorted(os.listdir(root)):
        vdir = os.path.join(root, name)
        if not os.path.isdir(vdir) or name.startswith("."):
            continue
        mpath = os.path.join(vdir, "manifest.yaml")
        if not os.path.isfile(mpath):
            _err(errors, name, "missing manifest.yaml")
            continue
        try:
            with open(mpath, "r", encoding="utf-8") as f:
                m = yaml.safe_load(f)
        except yaml.YAMLError as e:
            _err(errors, name, f"manifest.yaml is not valid YAML: {e}")
            continue
        if not isinstance(m, dict):
            _err(errors, name, "manifest.yaml must be a YAML mapping")
            continue

        if m.get("manifest_version") != 1:
            _err(errors, name, "manifest_version must equal 1 (Hermes rejects any other value)")

        mname = m.get("name")
        if not mname or not isinstance(mname, str):
            _err(errors, name, "missing 'name'")
        else:
            if not NAME_RE.match(mname):
                _err(errors, name, "name must match ^[A-Za-z0-9_-]+$")
            if mname != name:
                _err(errors, name, f"name '{mname}' != folder '{name}' (connect uses the folder name)")

        if not m.get("description"):
            _err(errors, name, "missing 'description'")

        # transport (required) — type + the type-specific launch field
        tr = m.get("transport")
        if not isinstance(tr, dict):
            _err(errors, name, "missing 'transport' mapping")
        else:
            ttype = tr.get("type")
            if ttype not in ("stdio", "http"):
                _err(errors, name, "transport.type must be 'stdio' or 'http'")
            elif ttype == "stdio" and not tr.get("command"):
                _err(errors, name, "stdio transport needs 'command'")
            elif ttype == "http" and not tr.get("url"):
                _err(errors, name, "http transport needs 'url'")

        # auth (optional; default none) — but api_key must actually declare credentials
        auth = m.get("auth")
        if auth is not None:
            if not isinstance(auth, dict):
                _err(errors, name, "'auth' must be a mapping")
            else:
                atype = auth.get("type", "none")
                if atype not in ("api_key", "oauth", "none"):
                    _err(errors, name, "auth.type must be 'api_key', 'oauth', or 'none'")
                if atype == "api_key":
                    env = auth.get("env") or []
                    has_env = isinstance(env, list) and any(
                        isinstance(e, dict) and e.get("name") for e in env)
                    if not (has_env or auth.get("bearer_env")):
                        _err(errors, name, "api_key auth must declare credentials via 'env:' "
                                           "(each with a name) or 'bearer_env:'")

        # category (SuperCMO-only) — list[str] or str if present; drives approvals auto-gating
        cat = m.get("category")
        if cat is not None:
            cats = [cat] if isinstance(cat, str) else cat
            if not (isinstance(cats, list) and all(isinstance(c, str) for c in cats)):
                _err(errors, name, "category must be a string or a list of strings")

        # tools.default_enabled — list[str] if present
        tools = m.get("tools")
        if isinstance(tools, dict) and "default_enabled" in tools:
            de = tools.get("default_enabled")
            if not (isinstance(de, list) and all(isinstance(t, str) for t in de)):
                _err(errors, name, "tools.default_enabled must be a list of strings")

        # install (optional, self-hosted) — git only, with a pinned ref (never float)
        inst = m.get("install")
        if inst is not None:
            if not isinstance(inst, dict) or inst.get("type") != "git":
                _err(errors, name, "install.type must be 'git'")
            else:
                if not inst.get("url"):
                    _err(errors, name, "install needs 'url'")
                if not inst.get("ref"):
                    _err(errors, name, "install needs a pinned 'ref' (tag/sha) — never float")
    return errors


def check_plugins(repo_root):
    """Validate every hermes-plugins/<name>/ has plugin.yaml + an __init__.py with a register hook."""
    errors = []
    root = os.path.join(repo_root, "hermes-plugins")
    if not os.path.isdir(root):
        return errors
    for name in sorted(os.listdir(root)):
        pdir = os.path.join(root, name)
        if not os.path.isdir(pdir) or name.startswith((".", "__")):
            continue
        if not os.path.isfile(os.path.join(pdir, "plugin.yaml")):
            _err(errors, name, "hermes plugin missing plugin.yaml")
        init = os.path.join(pdir, "__init__.py")
        if not os.path.isfile(init):
            _err(errors, name, "hermes plugin missing __init__.py")
            continue
        try:
            with open(init, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), init)
        except (OSError, SyntaxError) as e:
            _err(errors, name, f"__init__.py does not parse: {e}")
            continue
        if not any(isinstance(n, ast.FunctionDef) and n.name == "register"
                   for n in ast.walk(tree)):
            _err(errors, name, "__init__.py defines no `register(ctx)` hook (Hermes plugin entry point)")
    return errors


def selftest() -> bool:
    """Build throwaway manifests + plugins in a temp tree and assert the gate's verdicts —
    a good one passes, each violation class is caught. Mirrors listing_gate.py --selftest."""
    import shutil
    import tempfile

    tmp = tempfile.mkdtemp(prefix="check_extensions_selftest_")

    def mk_manifest(name, text):
        d = os.path.join(tmp, "optional-mcps", name)
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "manifest.yaml"), "w", encoding="utf-8") as f:
            f.write(text)

    def mk_plugin(name, init_body="def register(ctx):\n    pass\n", with_yaml=True):
        d = os.path.join(tmp, "hermes-plugins", name)
        os.makedirs(d, exist_ok=True)
        if with_yaml:
            with open(os.path.join(d, "plugin.yaml"), "w", encoding="utf-8") as f:
                f.write(f"name: {name}\nversion: 1.0.0\ndescription: t\nkind: backend\n")
        with open(os.path.join(d, "__init__.py"), "w", encoding="utf-8") as f:
            f.write(init_body)

    # (name, want_pass) — a manifest/plugin "passes" if the gate emits no error tagged with it.
    good_http = ('manifest_version: 1\nname: good-http\ndescription: t\ncategory: [social, publish]\n'
                 'transport:\n  type: http\n  url: "https://x/mcp"\n'
                 'auth:\n  type: api_key\n  bearer_env: X_KEY\n  env:\n    - {name: X_KEY, prompt: k, secret: true}\n')
    good_stdio = ('manifest_version: 1\nname: good-stdio\ndescription: t\ncategory: [ads, spend]\n'
                  'install:\n  type: git\n  url: "https://x"\n  ref: "v1"\n'
                  'transport:\n  type: stdio\n  command: uv\nauth:\n  type: oauth\n')
    mk_manifest("good-http", good_http)
    mk_manifest("good-stdio", good_stdio)
    mk_manifest("badver", 'manifest_version: 2\nname: badver\ndescription: t\ntransport:\n  type: http\n  url: u\n')
    mk_manifest("mismatch", 'manifest_version: 1\nname: other\ndescription: t\ntransport:\n  type: http\n  url: u\n')
    mk_manifest("http-nourl", 'manifest_version: 1\nname: http-nourl\ndescription: t\ntransport:\n  type: http\n')
    mk_manifest("apikey-nocreds", 'manifest_version: 1\nname: apikey-nocreds\ndescription: t\n'
                'transport:\n  type: http\n  url: u\nauth:\n  type: api_key\n')
    mk_manifest("badcat", 'manifest_version: 1\nname: badcat\ndescription: t\ncategory: 5\n'
                'transport:\n  type: http\n  url: u\n')
    mk_manifest("floatinstall", 'manifest_version: 1\nname: floatinstall\ndescription: t\n'
                'install:\n  type: git\n  url: u\ntransport:\n  type: stdio\n  command: uv\n')
    mk_plugin("good-plugin")
    mk_plugin("noreg", init_body="def setup():\n    pass\n")
    mk_plugin("noyaml", with_yaml=False)

    want = {  # tag -> should it PASS (no error tagged with it)?
        "good-http": True, "good-stdio": True, "good-plugin": True,
        "badver": False, "mismatch": False, "http-nourl": False, "apikey-nocreds": False,
        "badcat": False, "floatinstall": False, "noreg": False, "noyaml": False,
    }
    ok = True
    try:
        errors = check_mcp_manifests(tmp) + check_plugins(tmp)  # errors are tagged by folder name
        tagged = {tag: any(e.startswith(f"{tag}:") for e in errors) for tag in want}
        for tag, want_pass in want.items():
            got_pass = not tagged[tag]
            mark = "ok " if got_pass == want_pass else "FAIL"
            if got_pass != want_pass:
                ok = False
            print(f"  [{mark}] {tag}: pass={got_pass} (want {want_pass})")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    print("✓ selftest PASSED" if ok else "❌ selftest FAILED")
    return ok


def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    errors = check_mcp_manifests(repo_root) + check_plugins(repo_root)
    if errors:
        print("❌ Extension gate FAILED — invalid connector manifest / plugin:")
        for e in errors:
            print(f"   {e}")
        print("   See docs/mcp-authoring-contract.md (MCP) / hermes-plugins/supercmo_media (plugin).")
        return 1
    print("✓ Extension gate PASSED (optional-mcps/ manifests + hermes-plugins/ structure valid).")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:      # verify the gate logic itself
        sys.exit(0 if selftest() else 1)
    sys.exit(main())
