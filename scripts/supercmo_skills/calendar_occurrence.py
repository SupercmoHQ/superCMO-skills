"""Pure time-math for the Unified Agentic Calendar's firing loop: what fires when.

next_occurrence() finds the next timestamp an event lands on, one-shot or recurring via RRULE
(RFC 5545, dateutil). due() layers the watermark (fired_through) on top so the firing loop
never re-fires an occurrence it already handled — it returns the EARLIEST unfired occurrence,
not the latest, so a recurring task that was missed for a while catches up one step at a time
rather than skipping straight to "now". classify_missed() decides whether a late-discovered
occurrence is still worth firing or should be marked missed instead.

No I/O, no store access — only Event in, a decision out. The watermark write and the
missed-vs-fire policy per kind (posts never late-fire; tasks skip ahead) belong to the firing engine.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from dateutil.rrule import rrulestr

from supercmo_skills.calendar_store import Event

_EPOCH = datetime.min.replace(tzinfo=timezone.utc)  # "beginning of time" watermark sentinel


def next_occurrence(ev: Event, after: datetime) -> datetime | None:
    if ev.rrule is None:
        return ev.at if ev.at is not None and ev.at > after else None
    return rrulestr(ev.rrule, dtstart=ev.at).after(after)  # strictly after; None if exhausted


def due(ev: Event, now: datetime) -> datetime | None:
    if ev.status != "scheduled":
        return None
    occurrence = next_occurrence(ev, ev.fired_through or _EPOCH)
    return occurrence if occurrence is not None and occurrence <= now else None


def classify_missed(ev: Event, fired: datetime, now: datetime,
                     grace: timedelta = timedelta(minutes=10)) -> bool:
    return now - fired > grace
