"""Scheduling service — conflict detection using the new Lesson model.

Overlap is computed as the half-open range [start_time, start_time + duration_minutes)
Two lessons overlap iff:  a.start < b.end  AND  a.end > b.start
Back-to-back (a.end == b.start) is NOT a conflict.
"""

from datetime import date, datetime, time, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.class_enrollment import ClassEnrollment
from app.models.lesson import Lesson


def _add_minutes(start: time, minutes: int) -> time:
    """Add minutes to a TIME, returning a TIME (single-day arithmetic)."""
    anchor = datetime.combine(date.today(), start)
    return (anchor + timedelta(minutes=minutes)).time()


async def check_scheduling_conflicts(
    db: AsyncSession,
    teacher_id: UUID,
    day_of_week: int | None,
    start_time: str,
    duration_minutes: int,
    student_ids: list[UUID],
    exclude_lesson_id: UUID | None = None,
    center_id: UUID | None = None,
) -> list[dict]:
    """Check for teacher and student time conflicts against active Lessons.

    Args:
        teacher_id: UUID of the teacher
        day_of_week: 0=Monday … 6=Sunday. If None (one-off lesson), skip recurring conflict check.
        start_time: HH:MM string for the new lesson's start.
        duration_minutes: positive duration in minutes.
        exclude_lesson_id: lesson ID to exclude from conflict check (for updates).
        center_id: when provided, restrict conflict search to a single center.
    """
    if day_of_week is None:
        # One-off lessons: no recurring pattern to conflict with (date-based check not implemented here)
        return []

    st = time.fromisoformat(start_time)
    et = _add_minutes(st, duration_minutes)
    conflicts: list[dict] = []

    # Query all active recurring lessons on the same day
    base_query = select(Lesson).where(
        Lesson.day_of_week == day_of_week,
        Lesson.is_active == True,  # noqa: E712
        Lesson.start_time < et,
        Lesson.rrule.isnot(None),  # only recurring lessons have day_of_week conflicts
    )
    if center_id is not None:
        base_query = base_query.where(Lesson.center_id == center_id)
    if exclude_lesson_id:
        base_query = base_query.where(Lesson.id != exclude_lesson_id)

    # Teacher conflict
    teacher_result = await db.execute(base_query.where(Lesson.teacher_id == teacher_id))
    for lesson in teacher_result.scalars().all():
        lesson_end = _add_minutes(lesson.start_time, lesson.duration_minutes)
        if lesson_end > st:
            class_name = lesson.title or (lesson.class_.name if lesson.class_ else str(lesson.id))
            conflicts.append({
                "type": "teacher",
                "lesson_id": str(lesson.id),
                "message": (
                    f"Teacher has lesson '{class_name}' at "
                    f"{lesson.start_time.strftime('%H:%M')}-{lesson_end.strftime('%H:%M')}"
                ),
            })

    # Student conflict — check via class_enrollments → class_id → lessons
    for student_id in student_ids:
        student_result = await db.execute(
            base_query
            .join(ClassEnrollment, ClassEnrollment.class_id == Lesson.class_id)
            .where(
                ClassEnrollment.student_id == student_id,
                ClassEnrollment.is_active == True,  # noqa: E712
            )
        )
        for lesson in student_result.scalars().all():
            if exclude_lesson_id and lesson.id == exclude_lesson_id:
                continue
            lesson_end = _add_minutes(lesson.start_time, lesson.duration_minutes)
            if lesson_end > st:
                class_name = lesson.title or (lesson.class_.name if lesson.class_ else str(lesson.id))
                conflicts.append({
                    "type": "student",
                    "student_id": str(student_id),
                    "lesson_id": str(lesson.id),
                    "message": (
                        f"Student has lesson '{class_name}' at "
                        f"{lesson.start_time.strftime('%H:%M')}-{lesson_end.strftime('%H:%M')}"
                    ),
                })

    return conflicts
