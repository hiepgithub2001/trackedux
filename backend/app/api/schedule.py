"""Schedule API route — weekly calendar data using Lesson + recurrence expansion."""

from datetime import date, timedelta
from uuid import UUID

from fastapi import APIRouter

from app.core.deps import CurrentUser, DbSession, get_center_id
from app.crud.lesson import list_lessons, load_overrides_for_week
from app.services.recurrence_service import compute_week_occurrences

router = APIRouter(prefix="/schedule", tags=["Schedule"])


def _format_time(t) -> str:
    if t is None:
        return ""
    return t.strftime("%H:%M")


def _derive_end_time(start: str, duration: int) -> str:
    from datetime import datetime
    dt = datetime.strptime(start, "%H:%M")
    from datetime import timedelta as td
    return (dt + td(minutes=duration)).strftime("%H:%M")


@router.get("/weekly")
async def get_weekly_schedule(
    db: DbSession,
    current_user: CurrentUser,
    week_start: date | None = None,
    teacher_id: UUID | None = None,
):
    """Get weekly calendar view data using the new Lesson + recurrence model."""
    center_id = get_center_id(current_user)

    if week_start is None:
        today = date.today()
        week_start = today - timedelta(days=today.weekday())  # Monday

    week_end = week_start + timedelta(days=6)

    # Load all active lessons for this center (optionally filtered by teacher)
    lessons = await list_lessons(
        db, center_id=center_id, teacher_id=teacher_id, is_active=True
    )

    # Load persisted occurrence overrides for the week (+ buffer for rescheduled)
    lesson_ids = [lesson.id for lesson in lessons]
    overrides = await load_overrides_for_week(db, lesson_ids, week_start, week_end, center_id)

    # Compute virtual occurrences via rrule expansion + override overlay
    occurrences = compute_week_occurrences(lessons, overrides, week_start, week_end)

    # Build lesson lookup for roster data
    lesson_map = {str(lesson.id): lesson for lesson in lessons}

    sessions = []
    for occ in occurrences:
        lesson = lesson_map.get(str(occ.lesson_id))
        if lesson is None:
            continue

        start_str = _format_time(occ.start_time)
        effective_date_iso = occ.effective_date.isoformat()

        # Build enrolled students roster (respects enrolled_since / unenrolled_at)
        students = []
        if lesson.class_ and lesson.class_.enrollments:
            for e in lesson.class_.enrollments:
                if not e.is_active:
                    continue
                if e.enrolled_since and occ.effective_date < e.enrolled_since:
                    continue
                if e.unenrolled_at and occ.effective_date >= e.unenrolled_at:
                    continue
                students.append({
                    "id": str(e.student_id),
                    "name": e.student.name if e.student else "",
                })

        sessions.append({
            # --- Identity ---
            "id": str(occ.lesson_id),
            "occurrence_id": occ.occurrence_id,
            "lesson_id": str(occ.lesson_id),
            "class_id": str(occ.class_id) if occ.class_id else None,
            # --- Display ---
            "name": occ.lesson_name,
            "teacher": {
                "id": str(lesson.teacher_id),
                "full_name": lesson.teacher.full_name if lesson.teacher else "Unknown",
                "color": lesson.teacher.color if lesson.teacher else None,
            },
            "students": students,
            # --- Scheduling ---
            "day_of_week": occ.effective_date.weekday(),
            "start_time": start_str,
            "duration_minutes": occ.duration_minutes,
            "end_time": _derive_end_time(start_str, occ.duration_minutes),
            "date": effective_date_iso,
            "original_date": occ.original_date.isoformat(),
            # --- Status ---
            "is_canceled": occ.is_canceled,
            "is_rescheduled": occ.is_rescheduled,
            "is_recurring": lesson.rrule is not None,
            "is_makeup": lesson.specific_date is not None,
        })

    return {
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "sessions": sessions,
    }
