"""SuperCMO generation MCP server package.

`main` is the console entrypoint (`[project.scripts] supercmo-skills = "supercmo_skills.mcp:main"`)
and the target of `python -m supercmo_skills.mcp` (see `__main__.py`).
"""
from .server import main

__all__ = ["main"]
