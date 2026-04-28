"""Seed script to create default admin user and sample data."""

import asyncio

from sqlalchemy import select

from app.core.security import hash_password
from app.crud.lesson_kind import find_or_create_lesson_kind
from app.db.session import async_session_factory
from app.models.user import User


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


async def seed_lesson_kinds():
    """Seed initial lesson kinds."""
    async with async_session_factory() as db:
        kinds = ["Beginner", "Elementary", "Intermediate", "Advanced"]
        for kind in kinds:
            await find_or_create_lesson_kind(db, kind)
        print("✅ Lesson kinds seeded")


async def main():
    """Run all seed operations."""
    print("🌱 Seeding database...")
    await seed_admin()
    await seed_lesson_kinds()
    print("🌱 Seeding complete!")


if __name__ == "__main__":
    asyncio.run(main())
