"""The MCP binding of the calendar toolset: the 4 contract tools register in the server's
registry with MCP-shaped schemas, operate on the ics store at SUPERCMO_CALENDAR_PATH, and the
handler round-trip (add → list → update → remove) works through the registry exactly as an MCP
client would drive it."""

from datetime import datetime, timedelta, timezone

import supercmo_skills.mcp.tools  # noqa: F401 — importing registers every tool
from supercmo_skills.mcp import registry
from supercmo_skills.tool_specs import CALENDAR_TOOL_SPECS

CAL_NAMES = [s["name"] for s in CALENDAR_TOOL_SPECS]


def test_calendar_tools_registered_with_mcp_schemas():
    by_name = {s["name"]: s for s in registry.schemas()}
    for spec in CALENDAR_TOOL_SPECS:
        assert spec["name"] in by_name, f"{spec['name']} not registered"
        got = by_name[spec["name"]]
        assert got["inputSchema"] == spec["input_schema"]  # key renamed, body untouched
        assert got["description"] == spec["description"]


def test_calendar_roundtrip_via_registry(tmp_path, monkeypatch):
    monkeypatch.setenv("SUPERCMO_CALENDAR_PATH", str(tmp_path / "calendar.ics"))
    at = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()

    added = registry.handler("calendar_add")({
        "kind": "post", "title": "mcp post", "at": at, "content": "hello",
        "channel": "x", "publish_tool": "mcp_anything_post",  # stored as declared (no host registry)
    })
    assert "error" not in added, added

    listed = registry.handler("calendar_list")({})
    assert listed["count"] == 1 and listed["events"][0]["publish_tool"] == "mcp_anything_post"

    updated = registry.handler("calendar_update")({"id": added["id"], "title": "renamed"})
    assert "error" not in updated, updated

    removed = registry.handler("calendar_remove")({"id": added["id"]})
    assert removed["status"] == "cancelled"
    assert registry.handler("calendar_list")({})["count"] == 0  # default filter = scheduled


def test_calendar_add_validation_still_enforced(tmp_path, monkeypatch):
    monkeypatch.setenv("SUPERCMO_CALENDAR_PATH", str(tmp_path / "calendar.ics"))
    bad = registry.handler("calendar_add")({"kind": "post", "title": "x", "content": "c",
                                            "channel": "x", "publish_tool": "t"})
    assert "error" in bad  # neither at nor rrule


def test_tools_call_iserror_reflects_success_and_failure(tmp_path, monkeypatch):
    """Through the REAL JSON-RPC dispatch (server.handle), not registry.handler directly: a
    successful calendar_add must come back isError: false (the server derives isError from `ok`,
    which the binding stamps), and a failing one isError: true. Regression for the bug where
    every successful calendar call reported isError: true."""
    from supercmo_skills.mcp import server

    monkeypatch.setenv("SUPERCMO_CALENDAR_PATH", str(tmp_path / "calendar.ics"))
    at = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()

    good = server.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {
        "name": "calendar_add",
        "arguments": {"kind": "task", "title": "t", "at": at, "prompt": "p"}}})
    assert good["result"]["isError"] is False, good

    bad = server.handle({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {
        "name": "calendar_add", "arguments": {"kind": "task", "title": "t", "prompt": "p"}}})
    assert bad["result"]["isError"] is True, bad
