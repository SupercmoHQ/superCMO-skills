"""ics event store — the canonical calendar for tasks and posts (Unified Agentic Calendar).

One standard iCalendar file is the single source of truth the calendar toolset writes to and
the wrapper's firing engine reads from (the wrapper stores it at
`HERMES_HOME/workspace/calendar.ics`; the MCP binding resolves SUPERCMO_CALENDAR_PATH). Using
a real .ics file (not a bespoke DB) means the calendar is directly readable by any calendar
app via the `supercmo serve` feed — no export step, no second format to keep in sync.

Needs the `calendar` extra (icalendar + python-dateutil): `pip install supercmo-skills[calendar]`.
The base package stays stdlib-only; the MCP server degrades gracefully when the extra is absent.

Ownership: only VEVENTs carrying X-SUPERCMO-KIND are ours. A user who hand-edits the file and
adds a normal event keeps it byte-for-byte across every read/write — every write re-serializes
the WHOLE parsed calendar, touching only the components we own.

DESCRIPTION composition: the ics DESCRIPTION property is generated at write time,
never stored raw. It is `prompt` (task) or `content` (post), plus — only when a last-run result
exists — the literal delimiter line `--- last run` followed by the result block. The canonical
copy of that block lives in X-SUPERCMO-LAST-RESULT; parsing splits DESCRIPTION on the delimiter
and keeps only the half before it, so prompt/content round-trip byte-clean even with a result
block attached (the block after the delimiter is display-only redundancy for calendar apps).

Every write is atomic (tmp file + os.replace) and serialized across processes with an flock on
a sibling `.<stem>.lock` file.
"""

from __future__ import annotations

import fcntl
import os
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import icalendar

PRODID = "-//SuperCMO//calendar//EN"
_LAST_RUN_DELIM = "--- last run"
_KIND_PROP = "X-SUPERCMO-KIND"


def _local_tz() -> str:
    """System local IANA zone name (resolved via the /etc/localtime symlink target); UTC if
    the host has no zoneinfo symlink (e.g. some containers)."""
    try:
        return str(Path("/etc/localtime").resolve()).rsplit("zoneinfo/", 1)[1]
    except (OSError, IndexError):
        return "UTC"


@dataclass
class Event:
    id: str = ""            # uuid4 hex; add() fills it in when blank
    kind: str = ""          # "task" | "post"
    title: str = ""
    at: datetime | None = None
    rrule: str | None = None
    timezone: str = field(default_factory=_local_tz)
    status: str = "scheduled"          # scheduled|done|failed|missed|cancelled
    prompt: str | None = None          # task
    content: str | None = None         # post
    media: list[str] = field(default_factory=list)
    channel: str | None = None
    publish_tool: str | None = None
    last_run: datetime | None = None
    last_status: str | None = None
    last_session: str | None = None
    fired_through: datetime | None = None
    result_url: str | None = None              # published post URL, parsed after a fire
    last_result_block: str | None = None        # X-SUPERCMO-LAST-RESULT (canonical last-run text)


def _get(v: icalendar.Event, prop: str) -> str | None:
    val = v.get(prop)
    return None if val is None else str(val)


def _require_aware(dt: datetime, field: str) -> datetime:
    """Every datetime ingress (write or read) must be tz-aware — naive datetimes are a bug,
    never silently absorbed (e.g. `.astimezone()` on a naive dt treats it as system-local)."""
    if dt.tzinfo is None:
        raise ValueError(f"{field}: naive datetime not allowed — must be timezone-aware")
    return dt


def _get_dt(v: icalendar.Event, prop: str) -> datetime | None:
    val = _get(v, prop)
    return None if val is None else _require_aware(datetime.fromisoformat(val), prop)


def _is_ours(v: icalendar.Event) -> bool:
    return v.get(_KIND_PROP) is not None


def _to_vevent(ev: Event) -> icalendar.Event:
    v = icalendar.Event()
    v.add("UID", ev.id)
    # RFC 5545 REQUIRES DTSTAMP on every VEVENT — the moment this representation of the
    # event was generated, not a stored field; every write/read/serialize stamps it fresh.
    v.add("DTSTAMP", datetime.now(timezone.utc))
    v.add("SUMMARY", ev.title)
    if ev.at is not None:
        v.add("DTSTART", _require_aware(ev.at, "at").astimezone(ZoneInfo(ev.timezone)))
    if ev.rrule is not None:
        v["RRULE"] = icalendar.vRecur.from_ical(ev.rrule)
    v.add("STATUS", "CANCELLED" if ev.status == "cancelled" else "CONFIRMED")
    v.add(_KIND_PROP, ev.kind)
    v.add("X-SUPERCMO-STATE", ev.status)

    body = (ev.prompt if ev.kind == "task" else ev.content) or ""
    if ev.last_result_block:
        body = f"{body}\n{_LAST_RUN_DELIM}\n{ev.last_result_block}"
        v.add("X-SUPERCMO-LAST-RESULT", ev.last_result_block)
    if body:
        v.add("DESCRIPTION", body)

    for m in ev.media:
        v.add("ATTACH", m)
    if ev.channel:
        v.add("CATEGORIES", [ev.channel])
        v.add("X-SUPERCMO-CHANNEL", ev.channel)
    if ev.publish_tool:
        v.add("X-SUPERCMO-PUBLISH-TOOL", ev.publish_tool)
    if ev.last_run is not None:
        v.add("X-SUPERCMO-LAST-RUN", _require_aware(ev.last_run, "last_run").isoformat())
    if ev.last_status:
        v.add("X-SUPERCMO-LAST-STATUS", ev.last_status)
    if ev.last_session:
        v.add("X-SUPERCMO-LAST-SESSION", ev.last_session)
    if ev.result_url:
        v.add("URL", ev.result_url)
    if ev.fired_through is not None:
        v.add("X-SUPERCMO-FIRED-THROUGH", _require_aware(ev.fired_through, "fired_through").isoformat())
    return v


def to_ics(events: list[Event]) -> bytes:
    """Build a standalone VCALENDAR (PRODID/VERSION headers, no foreign components) from a
    list of Events — the filtered-feed path in `serve` uses this to serialize a subscribable
    subset on the fly, sharing the exact VEVENT encoding `add`/`update` write to disk."""
    cal = icalendar.Calendar()
    cal.add("PRODID", PRODID)
    cal.add("VERSION", "2.0")
    for e in events:
        cal.add_component(_to_vevent(e))
    cal.add_missing_timezones()  # every TZID a DTSTART/etc. references needs a VTIMEZONE
    return cal.to_ical()


def _from_vevent(v: icalendar.Event) -> Event:
    kind = _get(v, _KIND_PROP) or ""
    desc = _get(v, "DESCRIPTION")
    body = desc
    marker = f"\n{_LAST_RUN_DELIM}\n"
    if desc is not None and marker in desc:
        body = desc.split(marker, 1)[0]

    dtstart = v.get("DTSTART")
    at = None
    tz = _local_tz()
    if dtstart is not None:
        at = _require_aware(dtstart.dt, "at")
        tz = dtstart.params.get("TZID") or str(at.tzinfo)

    rrule_prop = v.get("RRULE")
    media_prop = v.get("ATTACH")
    if media_prop is None:
        media = []
    elif isinstance(media_prop, list):
        media = [str(m) for m in media_prop]
    else:
        media = [str(media_prop)]

    return Event(
        id=_get(v, "UID") or "",
        kind=kind,
        title=_get(v, "SUMMARY") or "",
        at=at,
        rrule=rrule_prop.to_ical().decode() if rrule_prop is not None else None,
        timezone=tz,
        status=_get(v, "X-SUPERCMO-STATE") or "",
        prompt=body if kind == "task" else None,
        content=body if kind == "post" else None,
        media=media,
        channel=_get(v, "X-SUPERCMO-CHANNEL"),
        publish_tool=_get(v, "X-SUPERCMO-PUBLISH-TOOL"),
        last_run=_get_dt(v, "X-SUPERCMO-LAST-RUN"),
        last_status=_get(v, "X-SUPERCMO-LAST-STATUS"),
        last_session=_get(v, "X-SUPERCMO-LAST-SESSION"),
        fired_through=_get_dt(v, "X-SUPERCMO-FIRED-THROUGH"),
        result_url=_get(v, "URL"),
        last_result_block=_get(v, "X-SUPERCMO-LAST-RESULT"),
    )


def _read_calendar(path: Path) -> icalendar.Calendar:
    if not path.exists():
        cal = icalendar.Calendar()
        cal.add("PRODID", PRODID)
        cal.add("VERSION", "2.0")
        return cal
    return icalendar.Calendar.from_ical(path.read_bytes())


def _write_calendar(path: Path, cal: icalendar.Calendar) -> None:
    cal.add_missing_timezones()  # RFC 5545 wants a VTIMEZONE for every TZID referenced
    tmp = path.with_suffix(".tmp")
    tmp.write_bytes(cal.to_ical())
    os.replace(tmp, path)  # atomic — readers never see a partial file


class CalendarStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock_path = self.path.with_name(f".{self.path.stem}.lock")

    @contextmanager
    def _locked(self):
        with open(self._lock_path, "a") as lockfile:
            fcntl.flock(lockfile.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lockfile.fileno(), fcntl.LOCK_UN)

    def list(self, *, kind: str | None = None, channel: str | None = None,
              status: str | None = None) -> list[Event]:
        cal = _read_calendar(self.path)
        events = [_from_vevent(c) for c in cal.walk("VEVENT") if _is_ours(c)]
        if kind is not None:
            events = [e for e in events if e.kind == kind]
        if channel is not None:
            events = [e for e in events if e.channel == channel]
        if status is not None:
            events = [e for e in events if e.status == status]
        return events

    def get(self, event_id: str) -> Event | None:
        return next((e for e in self.list() if e.id == event_id), None)

    def add(self, event: Event) -> Event:
        if not event.id:
            event = replace(event, id=uuid.uuid4().hex)
        with self._locked():
            cal = _read_calendar(self.path)
            cal.add_component(_to_vevent(event))
            _write_calendar(self.path, cal)
        return event

    def update(self, event_id: str, **fields) -> Event:
        with self._locked():
            cal = _read_calendar(self.path)
            comps = cal.subcomponents
            idx = next((i for i, c in enumerate(comps)
                        if _is_ours(c) and str(c.get("UID")) == event_id), None)
            if idx is None:
                raise KeyError(event_id)
            updated = replace(_from_vevent(comps[idx]), **fields)
            comps[idx] = _to_vevent(updated)
            _write_calendar(self.path, cal)
        return updated

    def remove(self, event_id: str) -> Event:
        return self.update(event_id, status="cancelled")
