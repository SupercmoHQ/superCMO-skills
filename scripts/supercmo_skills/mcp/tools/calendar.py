"""Unified Agentic Calendar tools — thin MCP binding over supercmo_skills.calendar_tools.

Store/validation logic lives in calendar_tools/calendar_store (the same implementation the
SuperCMO wrapper's Hermes plugin binds natively); this only declares the schemas and forwards
the calls. The store is one RFC 5545 ics file at SUPERCMO_CALENDAR_PATH (default
`~/.supercmo/workspace/calendar.ics` — deliberately the SuperCMO wrapper's calendar, so an MCP
client like Claude Code and a local `supercmo` install manage the SAME calendar, and the
wrapper's cron fires what either scheduled; writes are flock-serialized + atomic, so
cross-process sharing is safe).

Two deliberate MCP-surface limits, both host-bound by nature (not regressions):
- `publish_tool` is stored as declared — an MCP server cannot see the CLIENT's other tools, so
  schedule-time liveness validation only happens in the wrapper's native binding.
- Nothing here FIRES events. Firing runs real agent turns and needs an always-on host
  (`supercmo cron run` / `supercmo serve`); this surface manages the schedule.

Needs the `calendar` extra: without icalendar + python-dateutil the tools still register and
return an actionable install hint (same graceful posture as no_provider_configured).
"""

import os
from pathlib import Path

from .. import registry
from supercmo_skills import tool_specs

try:
    from supercmo_skills import calendar_tools as _ct
    from supercmo_skills.calendar_store import CalendarStore as _CalendarStore
    _IMPORT_ERROR = None
except ImportError as e:  # stdlib-only install (e.g. the vendored Claude plugin path)
    _ct = _CalendarStore = None
    _IMPORT_ERROR = str(e)

_DEPS_HINT = {
    "ok": False,
    "error": "calendar_deps_missing",
    "hint": "the calendar tools need the `calendar` extra: pip install 'supercmo-skills[calendar]' "
            "(icalendar + python-dateutil)",
}


def _store():
    path = os.environ.get("SUPERCMO_CALENDAR_PATH") or str(
        Path.home() / ".supercmo" / "workspace" / "calendar.ics")
    return _CalendarStore(Path(path))


def _mcp_schema(spec: dict) -> dict:
    # CALENDAR_TOOL_SPECS entries are Anthropic-shaped ({name, description, input_schema});
    # MCP wants inputSchema. Key rename only — the schema body passes through untouched.
    return {"name": spec["name"], "description": spec["description"],
            "inputSchema": spec["input_schema"]}


def _bind(fn):
    def handler(args):
        if _ct is None:
            return dict(_DEPS_HINT, detail=_IMPORT_ERROR)
        out = fn(_store(), **(args or {}))
        # The server's tools/call envelope derives isError from `ok` — the calendar_tools core
        # signals failure via an `error` key only (its dicts are shared with non-MCP bindings),
        # so stamp `ok` here or every SUCCESSFUL call reports isError: true to the client.
        return dict(out, ok="error" not in out)
    return handler


_HANDLERS = {
    "calendar_list": lambda store, **kw: _ct.list_events(store, **kw),
    "calendar_add": lambda store, **kw: _ct.add_event(store, **kw),
    "calendar_update": lambda store, **kw: _ct.update_event(store, **kw),
    "calendar_remove": lambda store, **kw: _ct.remove_event(store, **kw),
}

for _spec in tool_specs.CALENDAR_TOOL_SPECS:
    registry.register(_mcp_schema(_spec), _bind(_HANDLERS[_spec["name"]]))
