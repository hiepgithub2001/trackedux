"""Teacher CRUD database operations."""

from datetime import time
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.teacher import Teacher
from app.models.teacher_availability import TeacherAvailability
from app.schemas.teacher import AvailabilitySlot, TeacherCreate, TeacherUpdate


async def create_teacher(db: AsyncSession, data: TeacherCreate, center_id: UUID) -> Teacher:
    """Create a new teacher scoped to a center."""
    teacher_data = data.model_dump()
    if not teacher_data.get("color"):
        import random

        colors = [
            "#f5222d",
            "#fa541c",
            "#fa8c16",
            "#faad14",
            "#fadb14",
            "#a0d911",
            "#52c41a",
            "#13c2c2",
            "#1677ff",
            "#2f54eb",
            "#722ed1",
            "#eb2f96",
            "#f5222d",
            "#d4380d",
            "#d46b08",
            "#d48806",
            "#389e0d",
            "#08979c",
            "#0958d9",
            "#531dab",
        ]
        teacher_data["color"] = random.choice(colors)

    teacher = Teacher(**teacher_data, center_id=center_id)
    db.add(teacher)
    await db.commit()
    await db.refresh(teacher)
    return teacher


async def get_teacher_by_id(db: AsyncSession, teacher_id: UUID, center_id: UUID) -> Teacher | None:
    """Get teacher by ID scoped to center."""
    result = await db.execute(
        select(Teacher)
        .options(selectinload(Teacher.availability))
        .where(Teacher.id == teacher_id, Teacher.center_id == center_id)
    )
    return result.scalar_one_or_none()


async def list_teachers(db: AsyncSession, center_id: UUID, active_only: bool = False) -> list[Teacher]:
    """List all teachers scoped to a center."""
    query = (
        select(Teacher)
        .options(selectinload(Teacher.availability))
        .where(Teacher.center_id == center_id)
        .order_by(Teacher.full_name)
    )
    if active_only:
        query = query.where(Teacher.is_active == True)  # noqa: E712
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_teacher(db: AsyncSession, teacher_id: UUID, data: TeacherUpdate, center_id: UUID) -> Teacher | None:
    """Update teacher fields, scoped to center."""
    teacher = await get_teacher_by_id(db, teacher_id, center_id)
    if teacher is None:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(teacher, field, value)
    await db.commit()
    await db.refresh(teacher)
    return teacher


async def replace_availability(
    db: AsyncSession, teacher_id: UUID, slots: list[AvailabilitySlot], center_id: UUID
) -> Teacher | None:
    """Replace all availability slots for a teacher, scoped to center."""
    teacher = await get_teacher_by_id(db, teacher_id, center_id)
    if teacher is None:
        return None

    # Delete existing slots
    for slot in teacher.availability:
        await db.delete(slot)

    # Add new slots
    for slot_data in slots:
        s = TeacherAvailability(
            teacher_id=teacher_id,
            day_of_week=slot_data.day_of_week,
            start_time=time.fromisoformat(slot_data.start_time),
            end_time=time.fromisoformat(slot_data.end_time),
        )
        db.add(s)

    await db.commit()
    await db.refresh(teacher)
    return teacher
