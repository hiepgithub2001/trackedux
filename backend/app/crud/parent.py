"""Parent CRUD database operations."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.parent import Parent
from app.schemas.parent import ParentCreate, ParentUpdate


async def create_parent(db: AsyncSession, data: ParentCreate) -> Parent:
    """Create a new parent."""
    parent = Parent(**data.model_dump())
    db.add(parent)
    await db.commit()
    await db.refresh(parent)
    return parent


async def get_parent_by_id(db: AsyncSession, parent_id: UUID) -> Parent | None:
    """Get a parent by ID."""
    result = await db.execute(select(Parent).where(Parent.id == parent_id))
    return result.scalar_one_or_none()


async def list_parents(db: AsyncSession) -> list[Parent]:
    """List all parents."""
    result = await db.execute(select(Parent).order_by(Parent.full_name))
    return list(result.scalars().all())


async def update_parent(db: AsyncSession, parent_id: UUID, data: ParentUpdate) -> Parent | None:
    """Update parent fields."""
    parent = await get_parent_by_id(db, parent_id)
    if parent is None:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(parent, field, value)

    await db.commit()
    await db.refresh(parent)
    return parent
