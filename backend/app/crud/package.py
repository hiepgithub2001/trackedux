"""Package CRUD database operations — restructured for flexible course packages."""

from datetime import date
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.crud.class_session import compute_display_ids, get_class_session_by_id, list_class_sessions
from app.models.class_enrollment import ClassEnrollment
from app.models.class_session import ClassSession
from app.models.package import Package
from app.models.student import Student
from app.schemas.package import PackageCreate, PackageUpdate


async def update_package(db: AsyncSession, package_id: UUID, data: PackageUpdate, center_id: UUID) -> Package:
    package = await get_package_by_id(db, package_id, center_id)
    if not package:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Package not found")

    if data.number_of_lessons is not None:
        diff = data.number_of_lessons - package.number_of_lessons
        package.number_of_lessons = data.number_of_lessons
        package.remaining_sessions = max(0, package.remaining_sessions + diff)

    if data.tuition_fee is not None:
        package.price = data.tuition_fee

    if data.class_session_id is not None and data.class_session_id != package.class_session_id:
        cs = await get_class_session_by_id(db, data.class_session_id, center_id)
        if not cs:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

        enrollment_result = await db.execute(
            select(ClassEnrollment).where(
                ClassEnrollment.class_session_id == data.class_session_id,
                ClassEnrollment.student_id == package.student_id,
                ClassEnrollment.is_active == True,  # noqa: E712
            )
        )
        if enrollment_result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Student is not enrolled in the new class.",
            )
        package.class_session_id = data.class_session_id

    await db.commit()
    await db.refresh(package)
    return package


async def create_package(db: AsyncSession, data: PackageCreate, center_id: UUID) -> Package:
    """Create a flexible course package with enrollment validation and inline lesson kind create."""
    # 1. Verify student exists (within center)
    student = await db.get(Student, data.student_id)
    if student is None or student.center_id != center_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    # 2. Verify class exists (within center)
    cs = await get_class_session_by_id(db, data.class_session_id, center_id)
    if cs is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

    # 3. Compute display ID for error messages
    all_classes = await list_class_sessions(db, center_id=center_id, active_only=False)
    display_ids = compute_display_ids(all_classes)
    class_display_id = display_ids.get(cs.id, str(cs.id))

    # 4. Verify student is enrolled in class
    enrollment_result = await db.execute(
        select(ClassEnrollment).where(
            ClassEnrollment.class_session_id == data.class_session_id,
            ClassEnrollment.student_id == data.student_id,
            ClassEnrollment.is_active == True,  # noqa: E712
        )
    )
    if enrollment_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Student {student.name} is not enrolled in {class_display_id}. "
            "Enroll the student in the class first.",
        )

    # 6. Deactivate existing active package for student
    result = await db.execute(
        select(Package).where(Package.student_id == data.student_id, Package.is_active == True)  # noqa: E712
    )
    for old_pkg in result.scalars().all():
        old_pkg.is_active = False

    # 7. Create package scoped to center
    package = Package(
        student_id=data.student_id,
        class_session_id=data.class_session_id,
        number_of_lessons=data.number_of_lessons,
        remaining_sessions=data.number_of_lessons,
        price=data.tuition_fee,
        started_at=date.today(),
        center_id=center_id,
    )
    db.add(package)
    await db.commit()
    await db.refresh(package)
    return package


async def get_package_by_id(db: AsyncSession, package_id: UUID, center_id: UUID | None = None) -> Package | None:
    query = (
        select(Package)
        .options(
            selectinload(Package.student),
            selectinload(Package.payments),
            selectinload(Package.class_session).selectinload(ClassSession.teacher),
        )
        .where(Package.id == package_id)
    )
    if center_id is not None:
        query = query.where(Package.center_id == center_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def list_packages(
    db: AsyncSession,
    center_id: UUID | None = None,
    student_id: UUID | None = None,
    payment_status: str | None = None,
    class_session_id: UUID | None = None,
    active_only: bool = False,
) -> list[Package]:
    query = select(Package).options(
        selectinload(Package.student),
        selectinload(Package.class_session).selectinload(ClassSession.teacher),
    )
    if center_id is not None:
        query = query.where(Package.center_id == center_id)
    if student_id:
        query = query.where(Package.student_id == student_id)
    if payment_status:
        query = query.where(Package.payment_status == payment_status)
    if class_session_id:
        query = query.where(Package.class_session_id == class_session_id)
    if active_only:
        query = query.where(Package.is_active == True)  # noqa: E712
    query = query.order_by(Package.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_active_for_student(db: AsyncSession, student_id: UUID) -> Package | None:
    result = await db.execute(
        select(Package)
        .options(
            selectinload(Package.class_session).selectinload(ClassSession.teacher),
        )
        .where(Package.student_id == student_id, Package.is_active == True)  # noqa: E712
    )
    return result.scalar_one_or_none()

async def delete_package(db: AsyncSession, package_id: UUID, center_id: UUID) -> bool:
    package = await get_package_by_id(db, package_id, center_id)
    if not package:
        return False
    await db.delete(package)
    await db.commit()
    return True
