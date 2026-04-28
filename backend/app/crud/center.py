"""Center CRUD database operations."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.center import Center
from app.models.user import User


async def create_center(db: AsyncSession, name: str, registered_by_id: UUID) -> Center:
    """Create a new center and auto-generate code."""
    # Generate code like CTR-002
    result = await db.execute(select(func.count(Center.id)))
    count = result.scalar() or 0
    new_code = f"CTR-{count + 1:03d}"

    center = Center(
        name=name,
        code=new_code,
        registered_by_id=registered_by_id,
        is_active=True,
    )
    db.add(center)
    await db.commit()
    await db.refresh(center)
    return center


async def get_center(db: AsyncSession, center_id: UUID) -> Center | None:
    """Get a center by ID."""
    return await db.get(Center, center_id)


async def list_centers(db: AsyncSession, search: str | None = None, is_active: bool | None = None) -> list[dict]:
    """List centers with search and optional status filtering. Returns dictionaries with admin info."""
    query = select(Center, User).outerjoin(User, (Center.id == User.center_id) & (User.role == 'admin'))
    
    if search:
        search_pattern = f"%{search}%"
        query = query.where(Center.name.ilike(search_pattern) | Center.code.ilike(search_pattern))
        
    if is_active is not None:
        query = query.where(Center.is_active == is_active)
        
    query = query.order_by(Center.created_at.desc())
    
    result = await db.execute(query)
    
    # Map raw rows to dicts representing CenterListItem schema
    items = []
    for center, admin_user in result.all():
        item = {
            "id": center.id,
            "name": center.name,
            "code": center.code,
            "is_active": center.is_active,
            "registered_by_id": center.registered_by_id,
            "created_at": center.created_at,
            "updated_at": center.updated_at,
            "admin_username": admin_user.username if admin_user else None,
            "admin_email": admin_user.email if admin_user else None,
        }
        items.append(item)
        
    return items


async def patch_center(db: AsyncSession, center_id: UUID, **kwargs) -> Center | None:
    """Update a center."""
    center = await get_center(db, center_id)
    if not center:
        return None
        
    for key, value in kwargs.items():
        if hasattr(center, key):
            setattr(center, key, value)
            
    await db.commit()
    await db.refresh(center)
    return center
