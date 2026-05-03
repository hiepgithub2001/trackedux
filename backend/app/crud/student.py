"""Student CRUD database operations."""

from datetime import date
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.class_enrollment import ClassEnrollment
from app.models.student import Student
from app.schemas.student import StudentCreate, StudentUpdate


async def create_student(db: AsyncSession, data: StudentCreate, center_id: UUID) -> Student:
    """Create a new student scoped to a center."""
    class_ids = data.class_ids or []
    student_data = data.model_dump(exclude={"class_ids"})

    student = Student(
        **student_data,
        enrolled_at=date.today(),
        center_id=center_id,
    )
    db.add(student)
    await db.flush()

    for cid in class_ids:
        db.add(ClassEnrollment(class_id=cid, student_id=student.id, center_id=center_id))

    await db.commit()
    await db.refresh(student, ["enrollments"])
    return student


async def get_student_by_id(db: AsyncSession, student_id: UUID, center_id: UUID) -> Student | None:
    """Get a student by ID, scoped to a center."""
    result = await db.execute(
        select(Student)
        .options(selectinload(Student.enrollments))
        .where(Student.id == student_id, Student.center_id == center_id)
    )
    return result.scalar_one_or_none()


async def list_students(
    db: AsyncSession,
    center_id: UUID,
    status: str | None = None,
    search: str | None = None,
    sort_by: str = "name",
    sort_order: str = "asc",
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Student], int]:
    """List students with filtering, searching, sorting, and pagination — scoped to center."""
    query = select(Student).where(Student.center_id == center_id)

    # Filters
    if status:
        query = query.where(Student.enrollment_status == status)
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                func.unaccent(Student.name).ilike(func.unaccent(search_term)),
                func.unaccent(Student.nickname).ilike(func.unaccent(search_term)),
            )
        )

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Sorting
    sort_column = getattr(Student, sort_by, Student.name)
    if sort_order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # Pagination
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    students = list(result.scalars().all())

    return students, total


async def update_student(db: AsyncSession, student_id: UUID, data: StudentUpdate, center_id: UUID) -> Student | None:
    """Update student fields, scoped to center."""
    student = await get_student_by_id(db, student_id, center_id)
    if student is None:
        return None

    class_ids = data.class_ids
    update_data = data.model_dump(exclude_unset=True, exclude={"class_ids"})

    for field, value in update_data.items():
        setattr(student, field, value)

    if class_ids is not None:
        # Sync enrollments
        existing = {e.class_id: e for e in student.enrollments}
        new_set = set(class_ids)

        # Deactivate removed ones
        for cid, e in existing.items():
            if cid not in new_set:
                e.is_active = False
            else:
                e.is_active = True

        # Add new ones
        for cid in new_set:
            if cid not in existing:
                db.add(ClassEnrollment(class_id=cid, student_id=student.id, center_id=center_id))

    await db.commit()
    # Refresh to get updated enrollments
    await db.refresh(student, ["enrollments"])
    return student
