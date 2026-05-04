"""Recurrence service — RRULE expansion and occurrence overlay.

Occurrences are computed at read time from the lesson's RRULE.
No materialization job runs; only admin-mutated occurrences are persisted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta
from typing import TYPE_CHECKING

from dateutil.rrule import rrulestr

if TYPE_CHECKING:
    from app.models.lesson import Lesson
    from app.models.lesson_occurrence import LessonOccurrence

# RFC 5545 BYDAY map: dateutil weekday index → RRULE BYDAY token
_WEEKDAY_TO_BYDAY = {0: "MO", 1: "TU", 2: "WE", 3: "TH", 4: "FR", 5: "SA", 6: "SU"}
_BYDAY_TO_WEEKDAY = {v: k for k, v in _WEEKDAY_TO_BYDAY.items()}


@dataclass
class VirtualOccurrence:
    """A single occurrence of a lesson — virtual (computed) or persisted (overridden)."""

    lesson_id: str
    class_id: str | None
    original_date: date
    effective_date: date
    start_time: time
    duration_minutes: int
    is_canceled: bool = False
    is_rescheduled: bool = False
    occurrence_id: str | None = None
    # Populated from lesson for schedule rendering
    teacher_id: str = ""
    lesson_name: str = ""
    class_name: str | None = None
    rrule: str | None = None
    specific_date: date | None = None
    extra: dict = field(default_factory=dict)


def build_rrule_string(
    day_of_week: int,
    count: int | None = None,
    until: date | None = None,
    dtstart: date | None = None,
) -> str:
    """Build a minimal weekly RRULE string.

    Args:
        day_of_week: 0=Monday … 6=Sunday
        count: end after N occurrences (mutually exclusive with until)
        until: end on this date (mutually exclusive with count)
        dtstart: not embedded in the string; caller passes separately if needed
    """
    byday = _WEEKDAY_TO_BYDAY[day_of_week]
    parts = [f"FREQ=WEEKLY;BYDAY={byday}"]
    if count is not None:
        parts.append(f"COUNT={count}")
    elif until is not None:
        parts.append(f"UNTIL={until.strftime('%Y%m%d')}")
    return ";".join(parts)


def parse_rrule_day(rrule_str: str) -> int:
    """Extract the 0-indexed day-of-week from an RRULE BYDAY token.

    Returns 0 (Monday) if BYDAY is absent or unrecognised.
    """
    for part in rrule_str.split(";"):
        if part.startswith("BYDAY="):
            token = part.split("=", 1)[1].strip().upper()
            # Handle comma-separated values — take first
            first_token = token.split(",")[0]
            # Strip numeric prefix (e.g. "+2MO" → "MO")
            alpha = "".join(c for c in first_token if c.isalpha())
            return _BYDAY_TO_WEEKDAY.get(alpha, 0)
    return 0


def _find_dtstart(lesson: Lesson) -> datetime:
    """Determine the RRULE expansion anchor (dtstart).

    Uses the lesson's created_at date directly. This is correct for all RRULE
    types including COUNT-limited rules (COUNT starts counting from dtstart).
    """
    anchor_date = lesson.created_at.date() if hasattr(lesson, "created_at") and lesson.created_at else date.today()
    return datetime.combine(anchor_date, lesson.start_time)


def _add_minutes(t: time, minutes: int) -> time:
    anchor = datetime.combine(date.today(), t)
    return (anchor + timedelta(minutes=minutes)).time()


def compute_week_occurrences(
    lessons: list[Lesson],
    overrides: dict[tuple[str, date], LessonOccurrence],
    week_start: date,
    week_end: date,
) -> list[VirtualOccurrence]:
    """Compute all occurrences for a week, applying persisted overrides.

    Args:
        lessons: active Lesson objects for the center
        overrides: dict keyed on (lesson_id_str, original_date) → LessonOccurrence
        week_start: Monday of the week (inclusive)
        week_end: Sunday of the week (inclusive)

    Returns:
        List of VirtualOccurrence objects to display on the schedule.
        Canceled occurrences are included with is_canceled=True so callers
        can choose to display or hide them.
        Rescheduled occurrences appear under their effective_date week, not
        original_date week (callers filter by effective_date).
    """
    results: list[VirtualOccurrence] = []

    for lesson in lessons:
        if not lesson.is_active:
            continue

        class_name = lesson.class_.name if lesson.class_ else None
        display_name = lesson.title or class_name or ""
        teacher_id = str(lesson.teacher_id)
        lesson_id_str = str(lesson.id)

        if lesson.specific_date is not None:
            # One-off lesson — check if it falls in this week or has been rescheduled into it
            orig_date = lesson.specific_date
            key = (lesson_id_str, orig_date)
            override = overrides.get(key)
            occ = _build_occurrence(lesson, lesson_id_str, class_name, display_name, teacher_id, orig_date, override)
            # Include if effective_date falls in the requested week
            if week_start <= occ.effective_date <= week_end:
                results.append(occ)

        elif lesson.rrule:
            # Recurring — expand RRULE for the week
            dtstart = _find_dtstart(lesson)
            try:
                rule = rrulestr(lesson.rrule, dtstart=dtstart, ignoretz=True)
            except Exception:
                continue

            # Expand slightly wider to catch rescheduled occurrences from adjacent weeks
            expanded_dates = rule.between(
                datetime.combine(week_start - timedelta(days=7), time.min),
                datetime.combine(week_end + timedelta(days=7), time.max),
                inc=True,
            )

            for dt in expanded_dates:
                orig_date = dt.date()
                key = (lesson_id_str, orig_date)
                override = overrides.get(key)
                occ = _build_occurrence(
                    lesson, lesson_id_str, class_name, display_name, teacher_id, orig_date, override
                )
                # Include only occurrences whose effective_date falls in the requested week
                if week_start <= occ.effective_date <= week_end:
                    results.append(occ)

    return results


def _build_occurrence(
    lesson: Lesson,
    lesson_id_str: str,
    class_name: str | None,
    display_name: str,
    teacher_id: str,
    orig_date: date,
    override: LessonOccurrence | None,
) -> VirtualOccurrence:
    """Build a VirtualOccurrence, applying override if present."""
    if override is not None:
        effective_date = override.override_date if override.override_date else orig_date
        start_time = override.override_start_time if override.override_start_time else lesson.start_time
        is_canceled = override.status == "canceled"
        is_rescheduled = override.override_date is not None
        occurrence_id = str(override.id)
    else:
        effective_date = orig_date
        start_time = lesson.start_time
        is_canceled = False
        is_rescheduled = False
        occurrence_id = None

    return VirtualOccurrence(
        lesson_id=lesson_id_str,
        class_id=str(lesson.class_id) if lesson.class_id else None,
        original_date=orig_date,
        effective_date=effective_date,
        start_time=start_time,
        duration_minutes=lesson.duration_minutes,
        is_canceled=is_canceled,
        is_rescheduled=is_rescheduled,
        occurrence_id=occurrence_id,
        teacher_id=teacher_id,
        lesson_name=display_name,
        class_name=class_name,
        rrule=lesson.rrule,
        specific_date=lesson.specific_date,
    )
