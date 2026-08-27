"""Handler core for the shared calendar toolset (calendar_list/add/update/remove).

ONE implementation of the contract's semantics over the ics store, consumed by every local
surface: the SuperCMO wrapper's Hermes plugin (which injects its registry-liveness check as
`check_publish_tool`) and this package's own MCP server (no host registry — `publish_tool` is
stored as declared). The hosted product implements the same contract over its own store and
does not use this module.

Validation lives here (the store only enforces tz-awareness): callers pass exactly one of
`at`/`rrule`; a recurring event's `at` is always DERIVED as the creation-time anchor rather
than accepted from the caller, and that anchor is watermarked as already-fired so a brand-new
recurring event never fires at its own creation moment.

Uses icalendar + python-dateutil (part of the package's default install).
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Callable
from zoneinfo import ZoneInfo

from dateutil.rrule import rrulestr

from supercmo_skills.calendar_occurrence import next_occurrence
from supercmo_skills.calendar_store import CalendarStore, Event

_UPDATE_STATUS_VALUES = {"scheduled", "cancelled"}

# Optional hook: given a publish_tool name, return None if acceptable, else an error dict.
CheckPublishTool = Callable[[str], "dict | None"]


def _parse_dt(raw: str, tz_name: str) -> tuple[datetime | None, str | None]:
    """Parse `raw` as ISO-8601. A naive result gets the given timezone applied — friendlier
    than rejecting it, since the spec only needs the value to resolve to a real instant."""
    try:
        dt = datetime.fromisoformat(raw)
    except (TypeError, ValueError):
        return None, f"{raw!r} is not a valid ISO-8601 timestamp"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo(tz_name))
    return dt, None


def _event_dict(e: Event, occ: datetime | None) -> dict:
    return {
        "id": e.id, "kind": e.kind, "title": e.title,
        "at": e.at.isoformat() if e.at else None,
        "rrule": e.rrule, "timezone": e.timezone, "status": e.status,
        "prompt": e.prompt, "content": e.content, "media": e.media,
        "channel": e.channel, "publish_tool": e.publish_tool,
        "last_run": e.last_run.isoformat() if e.last_run else None,
        "last_status": e.last_status, "last_session": e.last_session,
        "fired_through": e.fired_through.isoformat() if e.fired_through else None,
        "result_url": e.result_url, "last_result_block": e.last_result_block,
        "next_occurrence": occ.isoformat() if occ else None,
    }


def list_events(store: CalendarStore, window_start=None, window_end=None, kind=None,
                channel=None, status=None, limit=50) -> dict:
    ws, err = _parse_dt(window_start, "UTC") if window_start else (None, None)
    if err:
        return {"error": err}
    we, err = _parse_dt(window_end, "UTC") if window_end else (None, None)
    if err:
        return {"error": err}

    events = store.list(kind=kind, channel=channel, status=status or "scheduled")
    rows = []
    for e in events:
        occ = next_occurrence(e, datetime.now(ZoneInfo(e.timezone)))
        if ws is not None or we is not None:
            # events with no next occurrence (e.g. a done one-shot) only show up window-less
            if occ is None or (ws is not None and occ < ws) or (we is not None and occ > we):
                continue
        rows.append((occ, e))
    rows.sort(key=lambda pair: (pair[0] is None, pair[0]))
    rows = rows[: limit or 50]
    return {"events": [_event_dict(e, occ) for occ, e in rows], "count": len(rows)}


def add_event(store: CalendarStore, kind, title, at=None, rrule=None, prompt=None,
              content=None, media=None, channel=None, publish_tool=None, timezone=None,
              check_publish_tool: CheckPublishTool | None = None) -> dict:
    if kind not in ("task", "post"):
        return {"error": f"kind must be 'task' or 'post', got {kind!r}"}
    if (at is None) == (rrule is None):  # both or neither
        return {"error": "exactly one of `at` or `rrule` is required"}
    if kind == "task" and not prompt:
        return {"error": "kind='task' requires `prompt`"}
    if kind == "post":
        missing = [f for f, v in (("content", content), ("channel", channel),
                                   ("publish_tool", publish_tool)) if not v]
        if missing:
            return {"error": f"kind='post' requires {', '.join(missing)}"}
        if check_publish_tool is not None:
            err = check_publish_tool(publish_tool)
            if err:
                return err

    tz_name = timezone or Event().timezone
    fired_through = None
    if rrule is not None:
        try:
            rrulestr(rrule)
        except Exception as e:
            return {"error": f"rrule {rrule!r} is not a valid recurrence rule: {e}"}
        anchor = datetime.now(ZoneInfo(tz_name))  # derived series anchor
        # Watermark the anchor itself as already-fired, or `due()`'s baseline (fired_through
        # or epoch) makes the anchor moment the FIRST fireable occurrence — a brand-new recurring
        # event would fire immediately instead of at its first real future occurrence.
        fired_through = anchor
    else:
        anchor, err = _parse_dt(at, tz_name)
        if err:
            return {"error": err}
        if anchor <= datetime.now(ZoneInfo(tz_name)):
            return {"error": f"`at` {at!r} must be in the future"}

    # `prompt`/`content` containing a literal "--- last run" line would be truncated by the
    # store's DESCRIPTION split — a known, accepted edge case, not fixed here.
    ev = Event(kind=kind, title=title, at=anchor, rrule=rrule, timezone=tz_name,
               prompt=prompt, content=content, media=media or [], channel=channel,
               publish_tool=publish_tool, fired_through=fired_through)
    added = store.add(ev)
    occ = next_occurrence(added, datetime.now(ZoneInfo(tz_name)))
    return {"id": added.id, "next_occurrence": occ.isoformat() if occ else None, "warnings": []}


def update_event(store: CalendarStore, id, title=None, at=None, rrule=None, prompt=None,
                 content=None, media=None, channel=None, publish_tool=None, timezone=None,
                 status=None, check_publish_tool: CheckPublishTool | None = None) -> dict:
    existing = store.get(id)
    if existing is None:
        return {"error": f"event {id!r} not found"}
    if status is not None and status not in _UPDATE_STATUS_VALUES:
        return {"error": f"status must be 'scheduled' or 'cancelled', got {status!r}"}
    if at is not None and rrule is not None:
        return {"error": "exactly one of `at` or `rrule` is required when changing the schedule"}

    tz_name = timezone or existing.timezone
    fields: dict = {}
    for key, val in (("title", title), ("prompt", prompt), ("content", content),
                      ("media", media), ("channel", channel), ("publish_tool", publish_tool),
                      ("timezone", timezone), ("status", status)):
        if val is not None:
            fields[key] = val

    if rrule is not None:
        try:
            rrulestr(rrule)
        except Exception as e:
            return {"error": f"rrule {rrule!r} is not a valid recurrence rule: {e}"}
        fields["rrule"] = rrule
        fields["at"] = datetime.now(ZoneInfo(tz_name))  # derived series anchor
        # Same anchor-never-fires watermark as add_event — an edit that (re)sets a
        # recurring rule must not make its own anchor moment immediately due.
        fields["fired_through"] = fields["at"]
    elif at is not None:
        dt, err = _parse_dt(at, tz_name)
        if err:
            return {"error": err}
        if dt <= datetime.now(ZoneInfo(tz_name)):
            return {"error": f"`at` {at!r} must be in the future"}
        fields["at"] = dt
        fields["rrule"] = None  # passing `at` makes it a one-shot — clears any prior rrule

    effective = replace(existing, **fields)
    if effective.kind == "task" and not effective.prompt:
        return {"error": "kind='task' requires `prompt`"}
    if effective.kind == "post":
        missing = [f for f in ("content", "channel", "publish_tool") if not getattr(effective, f)]
        if missing:
            return {"error": f"kind='post' requires {', '.join(missing)}"}
        if publish_tool is not None and check_publish_tool is not None:
            # re-validate only when this call changes it
            err = check_publish_tool(publish_tool)
            if err:
                return err

    updated = store.update(id, **fields)
    occ = next_occurrence(updated, datetime.now(ZoneInfo(updated.timezone)))
    return {"id": id, "next_occurrence": occ.isoformat() if occ else None}


def remove_event(store: CalendarStore, id) -> dict:
    if store.get(id) is None:
        return {"error": f"event {id!r} not found"}
    store.remove(id)
    return {"id": id, "status": "cancelled"}
