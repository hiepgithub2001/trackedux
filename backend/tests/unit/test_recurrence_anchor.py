"""Unit tests for the recurrence anchor — a schedule edit must not spawn past occurrences.

Regression: editing a recurring lesson's weekday expanded the new RRULE from
created_at, retroactively generating occurrences on the new weekday for past
weeks. Those phantom past occurrences got materialized as unmarked (pending).
Pinning ``recurrence_anchor`` forward keeps the changed rule forward-only.
"""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from dateutil.rrule import rrulestr

from app.services.recurrence_service import _find_dtstart


@dataclass
class _FakeLesson:
    """Minimal stand-in exposing the attributes _find_dtstart reads."""

    start_time: time
    created_at: datetime
    recurrence_anchor: date | None = None


def _expand(lesson: _FakeLesson, rrule: str, start: date, end: date) -> list[date]:
    dtstart = _find_dtstart(lesson)
    rule = rrulestr(rrule, dtstart=dtstart, ignoretz=True)
    return [
        dt.date()
        for dt in rule.between(
            datetime.combine(start, time.min),
            datetime.combine(end, time.max),
            inc=True,
        )
    ]


def test_changed_weekday_does_not_spawn_past_occurrences():
    today = date.today()
    created = today - timedelta(days=28)  # created four weeks ago
    lesson = _FakeLesson(
        start_time=time(9, 0),
        created_at=datetime.combine(created, time(9, 0)),
        # Schedule edit pinned the new (Wednesday) rule to today.
        recurrence_anchor=today,
    )

    # New rule is weekly on Wednesday; expand across the whole history window.
    occurrences = _expand(lesson, "FREQ=WEEKLY;BYDAY=WE", created, today)

    # No occurrence may predate the anchor — the past is never rewritten.
    assert all(d >= today for d in occurrences)


def test_without_anchor_falls_back_to_created_at():
    today = date.today()
    created = today - timedelta(days=28)
    lesson = _FakeLesson(
        start_time=time(9, 0),
        created_at=datetime.combine(created, time(9, 0)),
        recurrence_anchor=None,
    )

    # Legitimate reach-back: an unedited recurring lesson still surfaces its past
    # occurrences (needed so genuinely-missed lessons appear in Pending).
    occurrences = _expand(lesson, "FREQ=WEEKLY;BYDAY=MO", created, today)

    assert any(d < today for d in occurrences)
