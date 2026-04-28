"""LessonKind CRUD — find-or-create, list, search, normalization."""

import re
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lesson_kind import LessonKind


def normalize_lesson_kind_name(name: str) -> str:
    """Trim, collapse internal whitespace, and lowercase a lesson kind name."""
    return re.sub(r"\s+", " ", name.strip()).lower()


async def find_or_create_lesson_kind(db: AsyncSession, name: str, center_id: UUID) -> LessonKind:
    """Atomically find an existing lesson kind or create a new one, scoped to a center."""
    normalized = normalize_lesson_kind_name(name)
    display_name = re.sub(r"\s+", " ", name.strip())  # preserve casing

    # Try to find existing (within this center)
    result = await db.execute(
        select(LessonKind).where(LessonKind.name_normalized == normalized, LessonKind.center_id == center_id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    # Insert new
    new_kind = LessonKind(name=display_name, name_normalized=normalized, center_id=center_id)
    db.add(new_kind)
    try:
        await db.flush()
    except Exception:
        await db.rollback()
        result = await db.execute(
            select(LessonKind).where(LessonKind.name_normalized == normalized, LessonKind.center_id == center_id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing
        raise
    return new_kind


async def list_lesson_kinds(db: AsyncSession, center_id: UUID, search: str | None = None) -> list[LessonKind]:
    """List lesson kinds for a center, optionally filtered by search."""
    query = select(LessonKind).where(LessonKind.center_id == center_id).order_by(LessonKind.name)
    if search:
        pattern = f"%{search.strip().lower()}%"
        query = query.where(LessonKind.name_normalized.ilike(pattern))
    result = await db.execute(query)
    return list(result.scalars().all())
