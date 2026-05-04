"""Seed script to create default admin user and sample data."""

import asyncio
from uuid import UUID

from sqlalchemy import select

from app.core.security import hash_password
from app.crud.lesson_kind import find_or_create_lesson_kind
from app.db.session import async_session_factory
from app.models.center import Center
from app.models.user import User


async def seed_superadmin():
    """Create default superadmin user if not exists."""
    async with async_session_factory() as db:
        result = await db.execute(select(User).where(User.username == "superadmin"))
        existing = result.scalar_one_or_none()

        if existing:
            print("Superadmin user already exists, skipping.")
            return

        superadmin = User(
            username="superadmin",
            email="superadmin@trackedux.local",
            password_hash=hash_password("superadmin123"),
            role="superadmin",
            full_name="System Super Administrator",
            language="vi",
            is_active=True,
            center_id=None,
        )
        db.add(superadmin)
        await db.commit()
        print("✅ Superadmin user created (superadmin / superadmin123)")


async def seed_admin():
    """Create default admin user if not exists."""
    async with async_session_factory() as db:
        result = await db.execute(select(User).where(User.username == "admin"))
        existing = result.scalar_one_or_none()

        if existing:
            print("Admin user already exists, skipping.")
            return

        admin = User(
            username="admin",
            email="admin@trackedux.local",
            password_hash=hash_password("admin123"),
            role="admin",
            full_name="System Administrator",
            language="vi",
            is_active=True,
        )
        db.add(admin)
        await db.commit()
        print("✅ Admin user created (admin / admin123)")


async def seed_default_center() -> UUID:
    """Create default center if not exists, return its id.

    Also assigns the admin user to this center so tenant-scoped
    endpoints work (get_center_id requires a non-NULL center_id).
    """
    async with async_session_factory() as db:
        result = await db.execute(select(Center).where(Center.code == "DEMO"))
        existing = result.scalar_one_or_none()

        # Look up admin user
        admin_result = await db.execute(select(User).where(User.username == "admin"))
        admin = admin_result.scalar_one_or_none()

        if existing:
            # Ensure admin is assigned to this center (idempotent fix)
            if admin and admin.center_id != existing.id:
                admin.center_id = existing.id
                await db.commit()
            print("Default center already exists, skipping.")
            return existing.id

        center = Center(
            name="Demo Center",
            code="DEMO",
            registered_by_id=admin.id if admin else None,
            is_active=True,
        )
        db.add(center)
        await db.flush()

        # Assign admin user to this center
        if admin:
            admin.center_id = center.id

        await db.commit()
        await db.refresh(center)
        print("✅ Default center created (Demo Center / DEMO)")
        return center.id


async def seed_lesson_kinds(center_id: UUID):
    """Seed initial lesson kinds for the given center."""
    async with async_session_factory() as db:
        kinds = ["Beginner", "Elementary", "Intermediate", "Advanced"]
        for kind in kinds:
            await find_or_create_lesson_kind(db, kind, center_id)
        await db.commit()
        print("✅ Lesson kinds seeded")


async def main():
    """Run all seed operations."""
    print("🌱 Seeding database...")
    await seed_superadmin()
    await seed_admin()
    center_id = await seed_default_center()
    await seed_lesson_kinds(center_id)
    print("🌱 Seeding complete!")


if __name__ == "__main__":
    asyncio.run(main())
