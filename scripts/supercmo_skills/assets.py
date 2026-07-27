"""Locate + install the OSS assets the wheel ships (the Hermes binding plugin + media skills).

The wheel force-includes them under `supercmo_skills/_assets/`; this resolves that path so the
OSS app can copy them into HERMES_HOME without knowing the package layout. In a bare source
checkout (not pip-installed) `_assets` does not exist — `install_into` is then a no-op, which is
fine: assets only matter inside the installed OSS app.
"""
import shutil
from pathlib import Path

_ASSETS = Path(__file__).resolve().parent / "_assets"


def plugins_dir() -> Path:
    return _ASSETS / "plugins"


def skills_dir() -> Path:
    return _ASSETS / "skills"


def catalog_dir() -> Path:
    """The marketing MCP catalog (optional-mcps manifests); HERMES_OPTIONAL_MCPS points here."""
    return _ASSETS / "optional-mcps"


def mcp_server_dir() -> Path:
    """The bundled MCP server (media generation + analysis tools). config_layer materializes it
    into HERMES_HOME/mcp-server and wires an `mcp_servers` entry at server.py."""
    return _ASSETS / "mcp-server"


def install_into(home) -> list:
    """Copy the bundled plugins + skills + MCP catalog into a Hermes home. Returns plugin names."""
    home = Path(home)
    installed = []
    for kind in ("plugins", "skills", "optional-mcps"):
        src = _ASSETS / kind
        if not src.is_dir():
            continue
        dst = home / kind
        dst.mkdir(parents=True, exist_ok=True)
        for child in src.iterdir():
            if child.name == "__pycache__":
                continue
            target = dst / child.name
            if child.is_dir():
                shutil.copytree(child, target, dirs_exist_ok=True)
            else:
                shutil.copyfile(child, target)
            if kind == "plugins":
                installed.append(child.name)
    # The MCP server ships as ONE directory (server.py + registry.py + tools/), not a category of
    # children — copy it whole so config_layer can point mcp_servers at home/mcp-server/server.py.
    mcp_src = _ASSETS / "mcp-server"
    if mcp_src.is_dir():
        shutil.copytree(mcp_src, home / "mcp-server", dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return installed
