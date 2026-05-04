"""Unit tests for recurrence_service — RRULE expansion and override overlay."""

from datetime import date, time
from unittest.mock import MagicMock

from app.services.recurrence_service import (
    build_rrule_string,
    compute_week_occurrences,
    parse_rrule_day,
)

# ──────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────


def make_lesson(
    lesson_id="aaaaaaaa-0000-0000-0000-000000000001",
    class_id="bbbbbbbb-0000-0000-0000-000000000001",
    teacher_id="cccccccc-0000-0000-0000-000000000001",
    rrule=None,
    specific_date=None,
    start_time=time(10, 0),
    duration_minutes=60,
    is_active=True,
    day_of_week=None,
    name="Test Class",
):
    lesson = MagicMock()
    lesson.id = lesson_id
    lesson.class_id = class_id
    lesson.teacher_id = teacher_id
    lesson.rrule = rrule
    lesson.specific_date = specific_date
    lesson.start_time = start_time
    lesson.duration_minutes = duration_minutes
    lesson.is_active = is_active
    lesson.day_of_week = day_of_week
    lesson.title = None
    lesson.class_ = MagicMock()
    lesson.class_.name = name
    lesson.class_.enrollments = []
    lesson.teacher = MagicMock()
    lesson.teacher.full_name = "Teacher A"
    # For dtstart calculation
    lesson.created_at = MagicMock()
    lesson.created_at.date.return_value = date(2024, 1, 1)
    return lesson


# ──────────────────────────────────────────────────────────
# parse_rrule_day
# ──────────────────────────────────────────────────────────


def test_parse_rrule_day_monday():
    assert parse_rrule_day("FREQ=WEEKLY;BYDAY=MO") == 0


def test_parse_rrule_day_friday():
    assert parse_rrule_day("FREQ=WEEKLY;BYDAY=FR") == 4


def test_parse_rrule_day_sunday():
    assert parse_rrule_day("FREQ=WEEKLY;BYDAY=SU") == 6


def test_parse_rrule_day_missing_byday():
    # Should return 0 (Monday) as default
    assert parse_rrule_day("FREQ=WEEKLY") == 0


# ──────────────────────────────────────────────────────────
# build_rrule_string
# ──────────────────────────────────────────────────────────


def test_build_rrule_weekly_open():
    result = build_rrule_string(0)  # Monday, open-ended
    assert "FREQ=WEEKLY" in result
    assert "BYDAY=MO" in result
    assert "COUNT" not in result
    assert "UNTIL" not in result


def test_build_rrule_with_count():
    result = build_rrule_string(2, count=10)  # Wednesday, 10 occurrences
    assert "BYDAY=WE" in result
    assert "COUNT=10" in result


def test_build_rrule_with_until():
    result = build_rrule_string(4, until=date(2025, 6, 30))  # Friday until date
    assert "BYDAY=FR" in result
    assert "UNTIL=20250630" in result


# ──────────────────────────────────────────────────────────
# compute_week_occurrences — recurring lesson
# ──────────────────────────────────────────────────────────


def test_recurring_monday_appears_in_correct_week():
    """A Monday recurring lesson must appear exactly once in a Monday-anchored week."""
    lesson = make_lesson(rrule="FREQ=WEEKLY;BYDAY=MO", day_of_week=0)
    week_start = date(2025, 5, 5)  # Monday 2025-05-05
    week_end = date(2025, 5, 11)
    results = compute_week_occurrences([lesson], {}, week_start, week_end)
    assert len(results) == 1
    assert results[0].effective_date.weekday() == 0  # Monday


def test_recurring_lesson_does_not_appear_in_wrong_week():
    """A Monday lesson must NOT appear in a Wednesday-anchored non-matching week."""
    lesson = make_lesson(rrule="FREQ=WEEKLY;BYDAY=MO;COUNT=3", day_of_week=0)
    # Week of 2025-05-07 (Wed) to 2025-05-13 — Monday 2025-05-12 falls here
    week_start = date(2025, 5, 7)
    week_end = date(2025, 5, 13)
    results = compute_week_occurrences([lesson], {}, week_start, week_end)
    # Should contain the Monday that falls inside this window (May 12)
    assert all(week_start <= o.effective_date <= week_end for o in results)


def test_inactive_lesson_excluded():
    lesson = make_lesson(rrule="FREQ=WEEKLY;BYDAY=TU", day_of_week=1, is_active=False)
    week_start = date(2025, 5, 5)
    week_end = date(2025, 5, 11)
    results = compute_week_occurrences([lesson], {}, week_start, week_end)
    assert len(results) == 0


# ──────────────────────────────────────────────────────────
# compute_week_occurrences — one-off lesson
# ──────────────────────────────────────────────────────────


def test_oneoff_appears_only_in_matching_week():
    """A one-off lesson on a specific Saturday must appear only in that week."""
    target_date = date(2025, 5, 10)  # Saturday
    lesson = make_lesson(specific_date=target_date)
    week_start = date(2025, 5, 5)
    week_end = date(2025, 5, 11)
    results = compute_week_occurrences([lesson], {}, week_start, week_end)
    assert len(results) == 1
    assert results[0].effective_date == target_date


def test_oneoff_not_in_different_week():
    """Same one-off lesson must NOT appear in a different week."""
    target_date = date(2025, 5, 10)
    lesson = make_lesson(specific_date=target_date)
    next_week_start = date(2025, 5, 12)
    next_week_end = date(2025, 5, 18)
    results = compute_week_occurrences([lesson], {}, next_week_start, next_week_end)
    assert len(results) == 0


# ──────────────────────────────────────────────────────────
# compute_week_occurrences — override overlay
# ──────────────────────────────────────────────────────────


def test_canceled_occurrence_is_flagged():
    """A canceled override must be returned with is_canceled=True."""
    lesson = make_lesson(rrule="FREQ=WEEKLY;BYDAY=MO", day_of_week=0)
    lesson_id = str(lesson.id)
    week_start = date(2025, 5, 5)
    week_end = date(2025, 5, 11)
    orig_date = date(2025, 5, 5)

    override = MagicMock()
    override.status = "canceled"
    override.override_date = None
    override.override_start_time = None
    override.id = "override-uuid-001"

    overrides = {(lesson_id, orig_date): override}
    results = compute_week_occurrences([lesson], overrides, week_start, week_end)

    assert len(results) == 1
    assert results[0].is_canceled is True
    assert results[0].is_rescheduled is False


def test_rescheduled_occurrence_appears_on_new_date():
    """A rescheduled occurrence must appear on override_date week, NOT original_date week."""
    lesson = make_lesson(rrule="FREQ=WEEKLY;BYDAY=MO", day_of_week=0)
    lesson_id = str(lesson.id)

    orig_date = date(2025, 5, 5)  # Monday week 1
    new_date = date(2025, 5, 14)  # Wednesday week 2

    override = MagicMock()
    override.status = "active"
    override.override_date = new_date
    override.override_start_time = None
    override.id = "override-uuid-002"

    overrides = {(lesson_id, orig_date): override}

    # Check week 1 (orig_date) — occurrence should NOT appear (moved away)
    week1_start = date(2025, 5, 5)
    week1_end = date(2025, 5, 11)
    results_w1 = compute_week_occurrences([lesson], overrides, week1_start, week1_end)
    # The rescheduled occurrence has effective_date=May 14, outside week1
    assert all(o.effective_date > week1_end for o in results_w1 if o.original_date == orig_date)

    # Check week 2 (override_date) — occurrence should appear
    week2_start = date(2025, 5, 12)
    week2_end = date(2025, 5, 18)
    results_w2 = compute_week_occurrences([lesson], overrides, week2_start, week2_end)
    rescheduled = [o for o in results_w2 if o.original_date == orig_date]
    assert len(rescheduled) == 1
    assert rescheduled[0].effective_date == new_date
    assert rescheduled[0].is_rescheduled is True


def test_series_edit_does_not_override_occurrence_record():
    """After series start_time is updated, persisted override still wins over new series rule."""
    # Lesson series now uses 14:00 (updated via series edit)
    lesson = make_lesson(rrule="FREQ=WEEKLY;BYDAY=MO", day_of_week=0, start_time=time(14, 0))
    lesson_id = str(lesson.id)
    orig_date = date(2025, 5, 5)

    # Persisted override was created when start_time was 10:00 (before series edit)
    override = MagicMock()
    override.status = "active"
    override.override_date = None
    override.override_start_time = time(10, 0)  # Old time from when occurrence was persisted
    override.id = "override-uuid-003"

    overrides = {(lesson_id, orig_date): override}
    week_start = date(2025, 5, 5)
    week_end = date(2025, 5, 11)
    results = compute_week_occurrences([lesson], overrides, week_start, week_end)

    assert len(results) == 1
    # Override start_time (10:00) wins over new lesson.start_time (14:00)
    assert results[0].start_time == time(10, 0)
