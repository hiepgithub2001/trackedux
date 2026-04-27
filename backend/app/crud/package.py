"""Package CRUD database operations."""
from datetime import date
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.package import Package
from app.schemas.package import PackageCreate


async def create_package(db: AsyncSession, data: PackageCreate) -> Package:
    # Deactivate previous active package
    result = await db.execute(select(Package).where(Package.student_id == data.student_id, Package.is_active == True))
    for old_pkg in result.scalars().all():
        old_pkg.is_active = False

    package = Package(
        student_id=data.student_id, total_sessions=data.total_sessions,
        remaining_sessions=data.total_sessions, package_type=data.package_type,
        price=data.price, started_at=date.today(),
    )
    db.add(package)
    await db.commit()
    await db.refresh(package)
    return package


async def get_package_by_id(db: AsyncSession, package_id: UUID) -> Package | None:
    result = await db.execute(select(Package).options(selectinload(Package.student), selectinload(Package.payments)).where(Package.id == package_id))
    return result.scalar_one_or_none()


async def list_packages(db: AsyncSession, student_id: UUID | None = None, payment_status: str | None = None, active_only: bool = False) -> list[Package]:
    query = select(Package).options(selectinload(Package.student))
    if student_id:
        query = query.where(Package.student_id == student_id)
    if payment_status:
        query = query.where(Package.payment_status == payment_status)
    if active_only:
        query = query.where(Package.is_active == True)
    query = query.order_by(Package.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_active_for_student(db: AsyncSession, student_id: UUID) -> Package | None:
    result = await db.execute(select(Package).where(Package.student_id == student_id, Package.is_active == True))
    return result.scalar_one_or_none()
