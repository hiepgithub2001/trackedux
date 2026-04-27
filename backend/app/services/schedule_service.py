"""Scheduling service — conflict detection, capacity enforcement, availability validation."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.class_enrollment import ClassEnrollment
from app.models.class_session import ClassSession


async def check_scheduling_conflicts(
    db: AsyncSession,
    teacher_id: UUID,
    day_of_week: int,
    start_time: str,
    end_time: str,
    student_ids: list[UUID],
    exclude_class_id: UUID | None = None,
) -> list[dict]:
    """Check for teacher and student time conflicts."""
    from datetime import time

    st = time.fromisoformat(start_time)
    et = time.fromisoformat(end_time)
    conflicts = []

    # Teacher conflict check
    query = select(ClassSession).where(
        ClassSession.teacher_id == teacher_id,
        ClassSession.day_of_week == day_of_week,
        ClassSession.is_active == True,  # noqa: E712
        ClassSession.start_time < et,
        ClassSession.end_time > st,
    )
    if exclude_class_id:
        query = query.where(ClassSession.id != exclude_class_id)

    result = await db.execute(query)
    teacher_conflicts = result.scalars().all()
    for tc in teacher_conflicts:
        conflicts.append({"type": "teacher", "class_id": str(tc.id), "message": f"Teacher has class at {tc.start_time}-{tc.end_time}"})

    # Student conflict check
    for student_id in student_ids:
        student_classes = await db.execute(
            select(ClassSession)
            .join(ClassEnrollment)
            .where(
                ClassEnrollment.student_id == student_id,
                ClassEnrollment.is_active == True,  # noqa: E712
                ClassSession.day_of_week == day_of_week,
                ClassSession.is_active == True,  # noqa: E712
                ClassSession.start_time < et,
                ClassSession.end_time > st,
            )
        )
        for sc in student_classes.scalars().all():
            if exclude_class_id and sc.id == exclude_class_id:
                continue
            conflicts.append({
                "type": "student",
                "student_id": str(student_id),
                "class_id": str(sc.id),
                "message": f"Student has class at {sc.start_time}-{sc.end_time}",
            })

    return conflicts
