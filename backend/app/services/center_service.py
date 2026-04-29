"""Center business logic service."""

import random
import string
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.crud.center import create_center
from app.models.user import User


def _generate_password(length: int = 12) -> str:
    """Generate a random alphanumeric password."""
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))


async def create_center_with_admin(
    db: AsyncSession,
    center_name: str,
    admin_full_name: str,
    admin_username: str,
    admin_email: str | None,
    admin_password: str | None,
    registered_by_id: UUID,
) -> tuple[dict, dict]:
    """
    Atomically creates a Center and its admin User.
    Returns (center_dict, admin_credentials_dict).
    """
    # 1. Check if admin username or email already exists globally
    query = select(User).where(User.username == admin_username)
    if admin_email:
        query = query.where(User.email == admin_email, User.username != admin_username)  # Handle or condition properly

    result = await db.execute(select(User).where((User.username == admin_username) | (User.email == admin_email)))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username or email already exists in the system."
        )

    # 2. Create the center
    center = await create_center(db, center_name, registered_by_id)

    # 3. Create the admin user
    plain_password = admin_password if admin_password else _generate_password()
    admin_user = User(
        username=admin_username,
        email=admin_email,
        password_hash=hash_password(plain_password),
        role="admin",
        full_name=admin_full_name,
        language="vi",
        is_active=True,
        center_id=center.id,
    )
    db.add(admin_user)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create center and admin user"
        )

    await db.refresh(center)
    await db.refresh(admin_user)

    # Format the response tuple
    center_dict = {
        "id": center.id,
        "name": center.name,
        "code": center.code,
        "is_active": center.is_active,
        "registered_by_id": center.registered_by_id,
        "created_at": center.created_at,
        "updated_at": center.updated_at,
    }

    admin_credentials = {
        "username": admin_user.username,
        "temporary_password": plain_password,
        "note": "Please copy and save this password immediately. It will not be shown again.",
    }

    return center_dict, admin_credentials
