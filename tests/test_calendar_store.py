"""CalendarStore: the ics event store. Round-trip fidelity, atomic+locked writes,
foreign-VEVENT preservation, and the DESCRIPTION-composition rule are the core guarantees
the toolset and the firing engine build on."""

import subprocess
import sys
import textwrap
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import icalendar
import pytest

from supercmo_skills.calendar_store import CalendarStore, Event


def _dt(y, m, d, h, mi, tz="Asia/Kolkata"):
    return datetime(y, m, d, h, mi, tzinfo=ZoneInfo(tz))


@pytest.fixture
def store(tmp_path):
    return CalendarStore(tmp_path / "calendar.ics")


def test_round_trip_every_field_survives(store):
    ev = Event(
        kind="post",
        title="Launch tweet",
        at=_dt(2026, 9, 1, 9, 0),
        rrule=None,
        timezone="Asia/Kolkata",
        status="scheduled",
        content="Hello world",
        media=["file:///tmp/a.png", "file:///tmp/b.png"],
        channel="twitter",
        publish_tool="mcp_twitter_post",
        last_run=_dt(2026, 8, 20, 10, 0),
        last_status="ok",
        last_session="cal-abc123-202608201000",
        fired_through=_dt(2026, 8, 20, 9, 0),
        result_url="https://x.com/user/status/1",
    )
    added = store.add(ev)
    assert added.id  # generated

    listed = store.list()
    assert len(listed) == 1
    got = store.get(added.id)
    assert got is not None

    for e in (listed[0], got):
        assert e.id == added.id
        assert e.kind == "post"
        assert e.title == "Launch tweet"
        assert e.at == _dt(2026, 9, 1, 9, 0)
        assert e.at.tzinfo is not None
        assert e.rrule is None
        assert e.timezone == "Asia/Kolkata"
        assert e.status == "scheduled"
        assert e.content == "Hello world"
        assert e.prompt is None
        assert e.media == ["file:///tmp/a.png", "file:///tmp/b.png"]
        assert e.channel == "twitter"
        assert e.publish_tool == "mcp_twitter_post"
        assert e.last_run == _dt(2026, 8, 20, 10, 0)
        assert e.last_status == "ok"
        assert e.last_session == "cal-abc123-202608201000"
        assert e.fired_through == _dt(2026, 8, 20, 9, 0)
        assert e.result_url == "https://x.com/user/status/1"


def test_task_kind_round_trips_prompt_not_content(store):
    ev = Event(kind="task", title="Audit", at=_dt(2026, 9, 1, 9, 0), prompt="Run the audit")
    added = store.add(ev)
    got = store.get(added.id)
    assert got.prompt == "Run the audit"
    assert got.content is None


def test_recurring_event_rrule_and_anchor_round_trip(store):
    anchor = _dt(2026, 9, 7, 9, 0)  # a Monday, matching BYDAY=MO below
    ev = Event(kind="task", title="Weekly report", at=anchor, rrule="FREQ=WEEKLY;BYDAY=MO",
               prompt="write the report")
    added = store.add(ev)
    got = store.get(added.id)
    assert got.at == anchor
    # verify RRULE semantics via dateutil rather than byte equality
    from dateutil.rrule import rrulestr
    expanded = list(rrulestr(got.rrule, dtstart=got.at))[:2]
    assert expanded[0] == anchor
    assert expanded[1] == anchor + timedelta(days=7)


# --- RFC 5545 conformance — DTSTAMP on every VEVENT, VTIMEZONE for every TZID used ---

def test_every_vevent_has_dtstamp(store):
    store.add(Event(kind="task", title="t1", at=_dt(2026, 9, 1, 9, 0), prompt="p"))
    store.add(Event(kind="post", title="p1", at=_dt(2026, 9, 2, 9, 0), content="c"))
    cal = icalendar.Calendar.from_ical(store.path.read_bytes())
    vevents = cal.walk("VEVENT")
    assert len(vevents) == 2
    for v in vevents:
        assert v.get("DTSTAMP") is not None


def test_dtstamp_refreshed_on_update(store):
    added = store.add(Event(kind="task", title="t1", at=_dt(2026, 9, 1, 9, 0), prompt="p"))
    cal = icalendar.Calendar.from_ical(store.path.read_bytes())
    first_stamp = next(v for v in cal.walk("VEVENT") if str(v.get("UID")) == added.id).get("DTSTAMP").dt
    store.update(added.id, title="t1 v2")
    cal2 = icalendar.Calendar.from_ical(store.path.read_bytes())
    second_stamp = next(v for v in cal2.walk("VEVENT") if str(v.get("UID")) == added.id).get("DTSTAMP").dt
    assert second_stamp >= first_stamp  # re-stamped, not carried over stale


def test_write_adds_vtimezone_for_non_utc_event(store):
    """A non-UTC (Asia/Kolkata) DTSTART needs a VTIMEZONE component or strict ics readers can't
    resolve the TZID — `add_missing_timezones()` must run before every disk write."""
    store.add(Event(kind="task", title="IST task", at=_dt(2026, 9, 1, 9, 0, tz="Asia/Kolkata"),
                    timezone="Asia/Kolkata", prompt="p"))
    cal = icalendar.Calendar.from_ical(store.path.read_bytes())
    assert cal.walk("VTIMEZONE"), "expected a VTIMEZONE component for the Asia/Kolkata TZID"
    assert cal.get_missing_tzids() == set()


def test_write_no_vtimezone_needed_for_utc_only_event(store):
    # UTC needs no VTIMEZONE (icalendar represents it with a bare "Z" DTSTART) — add_missing_
    # timezones() must be a no-op here, not fabricate one for nothing.
    store.add(Event(kind="task", title="UTC task", at=_dt(2026, 9, 1, 9, 0, tz="UTC"),
                    timezone="UTC", prompt="p"))
    cal = icalendar.Calendar.from_ical(store.path.read_bytes())
    assert cal.walk("VTIMEZONE") == []


def test_to_ics_feed_also_gets_vtimezone_and_dtstamp(store):
    # The filtered-feed path (serve.py) builds its own standalone Calendar via to_ics() rather
    # than reading the on-disk file — it needs the same VTIMEZONE treatment.
    from supercmo_skills.calendar_store import to_ics

    added = store.add(Event(kind="task", title="IST task",
                            at=_dt(2026, 9, 1, 9, 0, tz="Asia/Kolkata"),
                            timezone="Asia/Kolkata", prompt="p"))
    cal = icalendar.Calendar.from_ical(to_ics([added]))
    assert cal.walk("VTIMEZONE")
    assert cal.walk("VEVENT")[0].get("DTSTAMP") is not None


def test_add_with_naive_at_raises(store):
    naive = datetime(2026, 9, 1, 9, 0)  # no tzinfo
    with pytest.raises(ValueError, match="at"):
        store.add(Event(kind="task", title="x", at=naive, prompt="p"))


def test_update_with_naive_last_run_raises(store):
    added = store.add(Event(kind="task", title="x", at=_dt(2026, 9, 1, 9, 0), prompt="p"))
    naive = datetime(2026, 8, 20, 10, 0)
    with pytest.raises(ValueError, match="last_run"):
        store.update(added.id, last_run=naive)


def test_update_with_naive_fired_through_raises(store):
    added = store.add(Event(kind="task", title="x", at=_dt(2026, 9, 1, 9, 0), prompt="p"))
    naive = datetime(2026, 8, 20, 9, 0)
    with pytest.raises(ValueError, match="fired_through"):
        store.update(added.id, fired_through=naive)


def test_corrupted_file_naive_last_run_raises_on_read(store):
    """Hand-edited/corrupted file with an offset-less X-SUPERCMO-LAST-RUN — read must fail
    loudly (the store's own writes always include an offset), not silently go naive."""
    added = store.add(Event(kind="task", title="x", at=_dt(2026, 9, 1, 9, 0), prompt="p"))
    raw = store.path.read_text()
    corrupted = raw.replace(
        f"UID:{added.id}",
        f"UID:{added.id}\r\nX-SUPERCMO-LAST-RUN:2026-08-20T10:00:00",  # no offset
    )
    store.path.write_text(corrupted)
    with pytest.raises(ValueError, match="X-SUPERCMO-LAST-RUN"):
        store.get(added.id)


def test_description_composition_and_last_result_round_trip(store):
    """DESCRIPTION = content/prompt + optional delimiter + last-run block;
    content/prompt round-trips byte-clean; the block is sourced from X-SUPERCMO-LAST-RESULT."""
    ev = Event(kind="post", title="Post", at=_dt(2026, 9, 1, 9, 0), content="The exact content.",
               channel="x", publish_tool="mcp_x_post",
               last_result_block="ok; session cal-abc-202608201000")
    added = store.add(ev)

    raw = store.path.read_text()
    assert "--- last run" in raw
    assert "X-SUPERCMO-LAST-RESULT" in raw

    got = store.get(added.id)
    assert got.content == "The exact content."  # byte-clean, no trailing delimiter/block
    assert got.last_result_block == "ok; session cal-abc-202608201000"


def test_c1_no_last_result_block_omits_delimiter(store):
    ev = Event(kind="post", title="Post", at=_dt(2026, 9, 1, 9, 0), content="Plain content")
    added = store.add(ev)
    raw = store.path.read_text()
    assert "--- last run" not in raw
    got = store.get(added.id)
    assert got.content == "Plain content"
    assert got.last_result_block is None


def test_atomic_write_no_tmp_leftover_after_success(store):
    store.add(Event(kind="task", title="x", at=_dt(2026, 9, 1, 9, 0), prompt="p"))
    assert not store.path.with_suffix(".tmp").exists()


def test_atomic_write_crash_between_tmp_and_replace_leaves_old_file_valid(store, monkeypatch):
    store.add(Event(kind="task", title="first", at=_dt(2026, 9, 1, 9, 0), prompt="p"))
    before = store.path.read_bytes()

    import supercmo_skills.calendar_store as calendar_store_mod

    def boom(*a, **k):
        raise OSError("simulated crash between tmp-write and replace")

    monkeypatch.setattr(calendar_store_mod.os, "replace", boom)
    with pytest.raises(OSError):
        store.add(Event(kind="task", title="second", at=_dt(2026, 9, 1, 9, 0), prompt="p"))

    # old file untouched — still valid ics with only the first event
    assert store.path.read_bytes() == before
    cal = icalendar.Calendar.from_ical(store.path.read_bytes())
    titles = [str(c.get("SUMMARY")) for c in cal.walk("VEVENT")]
    assert titles == ["first"]
    # the crashed write left its tmp artifact behind (never cleaned up mid-crash)
    assert store.path.with_suffix(".tmp").exists()


def test_update_changes_fields_and_survives_round_trip(store):
    added = store.add(Event(kind="task", title="Audit", at=_dt(2026, 9, 1, 9, 0), prompt="p"))
    updated = store.update(added.id, title="Audit v2", last_status="ok",
                            last_session="cal-x-1", status="done")
    assert updated.title == "Audit v2"
    got = store.get(added.id)
    assert got.title == "Audit v2"
    assert got.last_status == "ok"
    assert got.last_session == "cal-x-1"
    assert got.status == "done"
    assert got.prompt == "p"  # untouched fields survive


def test_update_missing_id_raises_keyerror(store):
    with pytest.raises(KeyError):
        store.update("does-not-exist", title="x")


def test_remove_marks_cancelled_and_keeps_in_file(store):
    added = store.add(Event(kind="task", title="Audit", at=_dt(2026, 9, 1, 9, 0), prompt="p"))
    removed = store.remove(added.id)
    assert removed.status == "cancelled"
    got = store.get(added.id)
    assert got is not None
    assert got.status == "cancelled"
    # still physically present in the file (kept for history), just filtered by status when asked
    assert store.list(status="cancelled") == [got]
    assert store.list(status="scheduled") == []


def test_list_filters_by_kind_channel_status(store):
    store.add(Event(kind="task", title="t1", at=_dt(2026, 9, 1, 9, 0), prompt="p"))
    store.add(Event(kind="post", title="p1", at=_dt(2026, 9, 2, 9, 0), content="c",
                     channel="twitter"))
    store.add(Event(kind="post", title="p2", at=_dt(2026, 9, 3, 9, 0), content="c",
                     channel="linkedin"))
    assert {e.title for e in store.list(kind="task")} == {"t1"}
    assert {e.title for e in store.list(kind="post")} == {"p1", "p2"}
    assert {e.title for e in store.list(channel="twitter")} == {"p1"}


def test_foreign_vevent_survives_round_trip_untouched(store):
    """A user hand-adds a plain VEVENT (no X-SUPERCMO-KIND) — it must never be modified,
    reordered, or dropped by our reads/writes."""
    cal = icalendar.Calendar()
    cal.add("PRODID", "-//Foreign//App//EN")
    cal.add("VERSION", "2.0")
    foreign = icalendar.Event()
    foreign.add("UID", "foreign-uid-1")
    foreign.add("SUMMARY", "Dentist appointment")
    foreign.add("DTSTART", _dt(2026, 10, 1, 14, 0))
    foreign.add("X-CUSTOM-FIELD", "user data we must not touch")
    cal.add_component(foreign)
    store.path.write_bytes(cal.to_ical())
    original_foreign_bytes = icalendar.Calendar.from_ical(
        store.path.read_bytes()
    ).walk("VEVENT")[0].to_ical()

    ours = store.add(Event(kind="task", title="Ours", at=_dt(2026, 9, 1, 9, 0), prompt="p"))
    store.update(ours.id, title="Ours v2")

    reparsed = icalendar.Calendar.from_ical(store.path.read_bytes())
    vevents = reparsed.walk("VEVENT")
    assert len(vevents) == 2
    foreign_after = next(c for c in vevents if str(c.get("UID")) == "foreign-uid-1")
    assert foreign_after.to_ical() == original_foreign_bytes
    assert str(foreign_after.get("X-CUSTOM-FIELD")) == "user data we must not touch"

    # list()/get() never surface the foreign event as ours
    assert all(e.id != "foreign-uid-1" for e in store.list())


def test_concurrent_add_blocks_on_flock_no_corruption(store, tmp_path):
    """A second process holding the sibling lock file blocks this process's add() until it
    releases — proving cross-process mutual exclusion, not just in-process safety."""
    import time

    lock_path = store._lock_path
    ready_path = tmp_path / "ready"
    hold_seconds = 1.5
    script = textwrap.dedent(f"""
        import fcntl, time
        f = open({str(lock_path)!r}, "a")
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        open({str(ready_path)!r}, "w").close()  # signal: lock is held
        time.sleep({hold_seconds})
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    """)
    proc = subprocess.Popen([sys.executable, "-c", script])
    deadline = time.monotonic() + 5
    while not ready_path.exists():
        assert time.monotonic() < deadline, "subprocess never acquired the lock"
        time.sleep(0.02)

    start = time.monotonic()
    added = store.add(Event(kind="task", title="blocked-add", at=_dt(2026, 9, 1, 9, 0), prompt="p"))
    elapsed = time.monotonic() - start
    proc.wait(timeout=5)

    assert elapsed >= hold_seconds * 0.6  # our add() genuinely waited on the lock
    assert proc.returncode == 0
    cal = icalendar.Calendar.from_ical(store.path.read_bytes())
    assert len(cal.walk("VEVENT")) == 1
    assert store.get(added.id).title == "blocked-add"
