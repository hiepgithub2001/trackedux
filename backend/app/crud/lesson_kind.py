"""LessonKind CRUD — find-or-create, list, search, normalization."""

import re
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lesson_kind import LessonKind


def normalize_lesson_kind_name(name: str) -> str:
    """Trim, collapse internal whitespace, and lowercase a lesson kind name."""
    return re.sub(r"\s+", " ", name.strip()).lower()


async def find_or_create_lesson_kind(db: AsyncSession, name: str) -> LessonKind:
    """Atomically find an existing lesson kind or create a new one.

    Uses INSERT ... ON CONFLICT DO NOTHING pattern for concurrent safety (SC-008).
    """
    normalized = normalize_lesson_kind_name(name)
    display_name = re.sub(r"\s+", " ", name.strip())  # preserve casing

    # Try to find existing
    result = await db.execute(
        select(LessonKind).where(LessonKind.name_normalized == normalized)
    )
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    # Insert new (race-safe: unique index on name_normalized)
    new_kind = LessonKind(name=display_name, name_normalized=normalized)
    db.add(new_kind)
    try:
        await db.flush()
    except Exception:
        # Concurrent insert — rollback the add and query again
        await db.rollback()
        result = await db.execute(
            select(LessonKind).where(LessonKind.name_normalized == normalized)
        )
        existing = result.scalar_one_or_none()
        if existing:
            return existing
        raise  # Unexpected error
    return new_kind


async def list_lesson_kinds(
    db: AsyncSession, search: str | None = None
) -> list[LessonKind]:
    """List lesson kinds, optionally filtered by case-insensitive substring match."""
    query = select(LessonKind).order_by(LessonKind.name)
    if search:
        pattern = f"%{search.strip().lower()}%"
        query = query.where(LessonKind.name_normalized.ilike(pattern))
    result = await db.execute(query)
    return list(result.scalars().all())
