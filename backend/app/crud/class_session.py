"""ClassSession CRUD database operations."""

from datetime import time
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.class_enrollment import ClassEnrollment
from app.models.class_session import ClassSession
from app.schemas.class_session import ClassSessionCreate


async def create_class_session(db: AsyncSession, data: ClassSessionCreate) -> ClassSession:
    """Create a new class session.

    No max-capacity is enforced (clarification 2026-04-27); all student_ids are enrolled.
    """
    cs = ClassSession(
        teacher_id=data.teacher_id,
        name=data.name,
        day_of_week=data.day_of_week,
        start_time=time.fromisoformat(data.start_time),
        duration_minutes=data.duration_minutes,
        is_recurring=data.is_recurring,
    )
    db.add(cs)
    await db.flush()

    for student_id in data.student_ids:
        enrollment = ClassEnrollment(class_session_id=cs.id, student_id=student_id)
        db.add(enrollment)

    await db.commit()
    await db.refresh(cs)
    return cs


async def get_class_session_by_id(db: AsyncSession, class_id: UUID) -> ClassSession | None:
    """Get class session by ID with enrollments."""
    result = await db.execute(
        select(ClassSession)
        .options(selectinload(ClassSession.teacher), selectinload(ClassSession.enrollments))
        .where(ClassSession.id == class_id)
    )
    return result.scalar_one_or_none()


async def list_class_sessions(
    db: AsyncSession,
    teacher_id: UUID | None = None,
    day_of_week: int | None = None,
    active_only: bool = True,
) -> list[ClassSession]:
    """List class sessions with filters (no class_type filter per clarification 2026-04-27)."""
    query = select(ClassSession).options(
        selectinload(ClassSession.teacher), selectinload(ClassSession.enrollments)
    )
    if teacher_id:
        query = query.where(ClassSession.teacher_id == teacher_id)
    if day_of_week is not None:
        query = query.where(ClassSession.day_of_week == day_of_week)
    if active_only:
        query = query.where(ClassSession.is_active == True)  # noqa: E712

    query = query.order_by(ClassSession.day_of_week, ClassSession.start_time)
    result = await db.execute(query)
    return list(result.scalars().all())


async def enroll_student(db: AsyncSession, class_id: UUID, student_id: UUID) -> ClassEnrollment:
    """Add a student to a class session."""
    enrollment = ClassEnrollment(class_session_id=class_id, student_id=student_id)
    db.add(enrollment)
    await db.commit()
    await db.refresh(enrollment)
    return enrollment


async def unenroll_student(db: AsyncSession, class_id: UUID, student_id: UUID) -> bool:
    """Remove a student from a class session."""
    result = await db.execute(
        select(ClassEnrollment).where(
            ClassEnrollment.class_session_id == class_id,
            ClassEnrollment.student_id == student_id,
        )
    )
    enrollment = result.scalar_one_or_none()
    if enrollment:
        enrollment.is_active = False
        await db.commit()
        return True
    return False


async def get_active_enrollment_count(db: AsyncSession, class_id: UUID) -> int:
    """Count active enrollments for a class."""
    result = await db.execute(
        select(func.count()).where(
            ClassEnrollment.class_session_id == class_id,
            ClassEnrollment.is_active == True,  # noqa: E712
        )
    )
    return result.scalar() or 0
