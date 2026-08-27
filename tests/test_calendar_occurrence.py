"""Occurrence-engine tests: one-shot, RRULE (daily/weekly BYDAY/monthly BYSETPOS=-1), DST
across the Europe/Berlin spring-forward boundary, watermark dedupe, and missed-grace
classification — the exact contract the firing loop depends on."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from supercmo_skills.calendar_occurrence import classify_missed, due, next_occurrence
from supercmo_skills.calendar_store import Event


def _dt(y, m, d, h, mi, tz="Asia/Kolkata"):
    return datetime(y, m, d, h, mi, tzinfo=ZoneInfo(tz))


# --- next_occurrence: one-shot ---

def test_next_occurrence_one_shot_future_returns_at():
    ev = Event(kind="task", at=_dt(2026, 9, 1, 9, 0))
    assert next_occurrence(ev, _dt(2026, 8, 1, 9, 0)) == _dt(2026, 9, 1, 9, 0)


def test_next_occurrence_one_shot_past_returns_none():
    ev = Event(kind="task", at=_dt(2026, 9, 1, 9, 0))
    assert next_occurrence(ev, _dt(2026, 9, 2, 9, 0)) is None


def test_next_occurrence_one_shot_exhausted_after_its_own_moment_returns_none():
    # a one-shot event has exactly one occurrence — once "after" reaches it, the series (of
    # one) is exhausted, same as any later "after".
    ev = Event(kind="task", at=_dt(2026, 9, 1, 9, 0))
    assert next_occurrence(ev, _dt(2026, 9, 1, 9, 0)) is None


# --- next_occurrence: recurring ---

def test_next_occurrence_daily():
    anchor = _dt(2026, 9, 1, 9, 0)
    ev = Event(kind="task", at=anchor, rrule="FREQ=DAILY")
    assert next_occurrence(ev, anchor) == anchor + timedelta(days=1)
    assert next_occurrence(ev, anchor + timedelta(days=1)) == anchor + timedelta(days=2)


def test_next_occurrence_weekly_byday():
    anchor = _dt(2026, 9, 7, 9, 0)  # Monday
    ev = Event(kind="task", at=anchor, rrule="FREQ=WEEKLY;BYDAY=MO,WE,FR")
    assert next_occurrence(ev, anchor) == _dt(2026, 9, 9, 9, 0)  # Wednesday
    assert next_occurrence(ev, _dt(2026, 9, 9, 9, 0)) == _dt(2026, 9, 11, 9, 0)  # Friday
    assert next_occurrence(ev, _dt(2026, 9, 11, 9, 0)) == _dt(2026, 9, 14, 9, 0)  # next Monday


def test_next_occurrence_monthly_bysetpos_last_friday():
    anchor = _dt(2026, 1, 30, 9, 0)  # last Friday of January 2026
    ev = Event(kind="task", at=anchor, rrule="FREQ=MONTHLY;BYDAY=FR;BYSETPOS=-1")
    assert next_occurrence(ev, anchor) == _dt(2026, 2, 27, 9, 0)  # last Friday of February
    assert next_occurrence(ev, _dt(2026, 2, 27, 9, 0)) == _dt(2026, 3, 27, 9, 0)  # last Friday of March


def test_next_occurrence_dst_spring_forward_preserves_wall_clock_hour_changes_offset():
    """Europe/Berlin, daily 02:30, crossing the 2027-03-28 spring-forward day. dateutil
    carries the zoneinfo tzinfo through rrule arithmetic, so the wall-clock hour/minute never
    shifts — only the resolved UTC offset does, once the transition day is behind it."""
    tz = ZoneInfo("Europe/Berlin")
    anchor = datetime(2027, 3, 21, 2, 30, tzinfo=tz)  # Sunday, one week before the transition
    ev = Event(kind="task", at=anchor, rrule="FREQ=DAILY")

    before = next_occurrence(ev, datetime(2027, 3, 26, 2, 30, tzinfo=tz))  # Mar 27, still CET
    on_transition_day = next_occurrence(ev, before)  # Mar 28 — the transition day itself
    after = next_occurrence(ev, on_transition_day)  # Mar 29, now CEST

    for o in (before, on_transition_day, after):
        assert (o.hour, o.minute) == (2, 30)  # wall-clock time never shifts

    assert before.utcoffset() == timedelta(hours=1)  # CET
    assert on_transition_day.utcoffset() == timedelta(hours=1)  # still CET
    assert after.utcoffset() == timedelta(hours=2)  # CEST — offset changed, hour did not


# --- due(): status gating + watermark dedupe ---

def test_due_returns_none_for_non_scheduled_status():
    ev = Event(kind="task", at=_dt(2026, 9, 1, 9, 0), status="done")
    assert due(ev, _dt(2026, 9, 2, 9, 0)) is None


def test_due_one_shot_unfired_and_past_is_due():
    ev = Event(kind="task", at=_dt(2026, 9, 1, 9, 0), status="scheduled")
    assert due(ev, _dt(2026, 9, 1, 9, 5)) == _dt(2026, 9, 1, 9, 0)


def test_due_one_shot_future_is_not_due():
    ev = Event(kind="task", at=_dt(2026, 9, 1, 9, 0), status="scheduled")
    assert due(ev, _dt(2026, 8, 1, 9, 0)) is None


def test_due_watermark_dedupe_one_shot():
    ev = Event(kind="task", at=_dt(2026, 9, 1, 9, 0), status="scheduled",
                fired_through=_dt(2026, 9, 1, 9, 0))
    assert due(ev, _dt(2026, 9, 2, 9, 0)) is None  # already fired — watermark covers it


def test_due_recurring_returns_earliest_unfired_occurrence():
    anchor = _dt(2026, 9, 1, 9, 0)
    ev = Event(kind="task", at=anchor, rrule="FREQ=DAILY", status="scheduled",
               fired_through=anchor)  # day 1 already fired
    now = anchor + timedelta(days=3)  # three days have passed since
    assert due(ev, now) == anchor + timedelta(days=1)  # earliest unfired, not the latest


def test_due_recurring_none_once_watermark_caught_up():
    anchor = _dt(2026, 9, 1, 9, 0)
    ev = Event(kind="task", at=anchor, rrule="FREQ=DAILY", status="scheduled",
               fired_through=anchor + timedelta(days=3))
    assert due(ev, anchor + timedelta(days=3)) is None


# --- classify_missed(): grace boundary ---

def test_classify_missed_false_within_grace():
    fired = _dt(2026, 9, 1, 9, 0)
    assert classify_missed(Event(), fired, fired + timedelta(minutes=5)) is False


def test_classify_missed_false_exactly_at_grace_boundary():
    fired = _dt(2026, 9, 1, 9, 0)
    assert classify_missed(Event(), fired, fired + timedelta(minutes=10)) is False


def test_classify_missed_true_beyond_grace():
    fired = _dt(2026, 9, 1, 9, 0)
    assert classify_missed(Event(), fired, fired + timedelta(minutes=11)) is True


def test_classify_missed_respects_custom_grace():
    fired = _dt(2026, 9, 1, 9, 0)
    assert classify_missed(
        Event(), fired, fired + timedelta(minutes=2), grace=timedelta(minutes=1)
    ) is True
