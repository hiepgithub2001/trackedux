"""CRUD operations for the Class entity."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.class_ import Class
from app.models.class_enrollment import ClassEnrollment
from app.schemas.class_ import ClassCreate, ClassUpdate


async def create_class(db: AsyncSession, data: ClassCreate, center_id: uuid.UUID) -> Class:
    """Create a new class and enroll initial students."""
    class_ = Class(
        name=data.name,
        teacher_id=data.teacher_id,
        tuition_fee_per_lesson=data.tuition_fee_per_lesson,
        lesson_kind_id=data.lesson_kind_id,
        center_id=center_id,
    )
    db.add(class_)
    await db.flush()  # get class_.id

    for student_id in data.student_ids:
        enrollment = ClassEnrollment(
            class_session_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),  # placeholder legacy FK
            class_id=class_.id,
            student_id=student_id,
            center_id=center_id,
        )
        db.add(enrollment)

    await db.commit()
    await db.refresh(class_)
    return class_


async def get_class_by_id(
    db: AsyncSession, class_id: uuid.UUID, center_id: uuid.UUID
) -> Class | None:
    result = await db.execute(
        select(Class).where(Class.id == class_id, Class.center_id == center_id)
    )
    return result.scalar_one_or_none()


async def list_classes(
    db: AsyncSession,
    center_id: uuid.UUID,
    teacher_id: uuid.UUID | None = None,
    is_active: bool = True,
) -> list[Class]:
    q = select(Class).where(Class.center_id == center_id)
    if teacher_id is not None:
        q = q.where(Class.teacher_id == teacher_id)
    if is_active is not None:
        q = q.where(Class.is_active == is_active)
    result = await db.execute(q)
    return list(result.scalars().all())


async def update_class(
    db: AsyncSession, class_id: uuid.UUID, data: ClassUpdate, center_id: uuid.UUID
) -> Class | None:
    class_ = await get_class_by_id(db, class_id, center_id)
    if class_ is None:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(class_, field, value)
    await db.commit()
    await db.refresh(class_)
    return class_


async def deactivate_class(
    db: AsyncSession, class_id: uuid.UUID, center_id: uuid.UUID
) -> bool:
    class_ = await get_class_by_id(db, class_id, center_id)
    if class_ is None:
        return False
    class_.is_active = False
    await db.commit()
    return True


async def enroll_student(
    db: AsyncSession,
    class_id: uuid.UUID,
    student_id: uuid.UUID,
    center_id: uuid.UUID,
    enrolled_since: date | None = None,
) -> ClassEnrollment:
    # Check if already enrolled
    result = await db.execute(
        select(ClassEnrollment).where(
            ClassEnrollment.class_id == class_id,
            ClassEnrollment.student_id == student_id,
            ClassEnrollment.center_id == center_id,
        )
    )
    existing = result.scalar_one_or_none()
    if existing is not None:
        existing.is_active = True
        existing.enrolled_since = enrolled_since
        existing.unenrolled_at = None
        await db.commit()
        return existing

    enrollment = ClassEnrollment(
        class_session_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),  # placeholder legacy FK
        class_id=class_id,
        student_id=student_id,
        center_id=center_id,
        enrolled_since=enrolled_since,
    )
    db.add(enrollment)
    await db.commit()
    await db.refresh(enrollment)
    return enrollment


async def unenroll_student(
    db: AsyncSession,
    class_id: uuid.UUID,
    student_id: uuid.UUID,
    center_id: uuid.UUID,
    unenrolled_at: date | None = None,
) -> bool:
    result = await db.execute(
        select(ClassEnrollment).where(
            ClassEnrollment.class_id == class_id,
            ClassEnrollment.student_id == student_id,
            ClassEnrollment.center_id == center_id,
        )
    )
    enrollment = result.scalar_one_or_none()
    if enrollment is None:
        return False
    enrollment.is_active = False
    enrollment.unenrolled_at = unenrolled_at
    await db.commit()
    return True
