"""Scheduling service — conflict detection.

Overlap is computed as the half-open range [start_time, start_time + duration_minutes)
per the 2026-04-27 clarification. Two sessions overlap iff
    a.start < b.end  AND  a.end > b.start
where end = start + duration. Back-to-back (a.end == b.start) is NOT a conflict.
"""

from datetime import date, datetime, time, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.class_enrollment import ClassEnrollment
from app.models.class_session import ClassSession


def _add_minutes(start: time, minutes: int) -> time:
    """Add minutes to a TIME, returning a TIME (single-day arithmetic)."""
    anchor = datetime.combine(date.today(), start)
    return (anchor + timedelta(minutes=minutes)).time()


async def check_scheduling_conflicts(
    db: AsyncSession,
    teacher_id: UUID,
    day_of_week: int,
    start_time: str,
    duration_minutes: int,
    student_ids: list[UUID],
    exclude_class_id: UUID | None = None,
) -> list[dict]:
    """Check for teacher and student time conflicts.

    Args:
        start_time: HH:MM string for the new session's start.
        duration_minutes: positive duration in minutes.
    """
    st = time.fromisoformat(start_time)
    et = _add_minutes(st, duration_minutes)
    conflicts: list[dict] = []

    # Pull every active session on this day in one query, compute overlap in Python.
    # The model has no `end_time` column anymore (it's derived), so we can't filter
    # via SQL on the right edge. The active-day set is small (a few rows per day).
    base_query = select(ClassSession).where(
        ClassSession.day_of_week == day_of_week,
        ClassSession.is_active == True,  # noqa: E712
        ClassSession.start_time < et,
    )
    if exclude_class_id:
        base_query = base_query.where(ClassSession.id != exclude_class_id)

    teacher_result = await db.execute(base_query.where(ClassSession.teacher_id == teacher_id))
    for tc in teacher_result.scalars().all():
        tc_end = _add_minutes(tc.start_time, tc.duration_minutes)
        if tc_end > st:
            conflicts.append({
                "type": "teacher",
                "class_id": str(tc.id),
                "message": (
                    f"Teacher has class '{tc.name}' at "
                    f"{tc.start_time.strftime('%H:%M')}-{tc_end.strftime('%H:%M')}"
                ),
            })

    for student_id in student_ids:
        student_result = await db.execute(
            base_query.join(ClassEnrollment, ClassEnrollment.class_session_id == ClassSession.id)
            .where(
                ClassEnrollment.student_id == student_id,
                ClassEnrollment.is_active == True,  # noqa: E712
            )
        )
        for sc in student_result.scalars().all():
            if exclude_class_id and sc.id == exclude_class_id:
                continue
            sc_end = _add_minutes(sc.start_time, sc.duration_minutes)
            if sc_end > st:
                conflicts.append({
                    "type": "student",
                    "student_id": str(student_id),
                    "class_id": str(sc.id),
                    "message": (
                        f"Student has class '{sc.name}' at "
                        f"{sc.start_time.strftime('%H:%M')}-{sc_end.strftime('%H:%M')}"
                    ),
                })

    return conflicts
