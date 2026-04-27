"""Student CRUD database operations."""

from datetime import date
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student import Student
from app.schemas.student import StudentCreate, StudentUpdate


async def create_student(db: AsyncSession, data: StudentCreate) -> Student:
    """Create a new student."""
    student = Student(
        **data.model_dump(),
        enrolled_at=date.today(),
    )
    db.add(student)
    await db.commit()
    await db.refresh(student)
    return student


async def get_student_by_id(db: AsyncSession, student_id: UUID) -> Student | None:
    """Get a student by ID with parent relationship."""
    result = await db.execute(
        select(Student).where(Student.id == student_id)
    )
    return result.scalar_one_or_none()


async def list_students(
    db: AsyncSession,
    status: str | None = None,
    skill_level: str | None = None,
    search: str | None = None,
    sort_by: str = "name",
    sort_order: str = "asc",
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[Student], int]:
    """List students with filtering, searching, sorting, and pagination."""
    query = select(Student)

    # Filters
    if status:
        query = query.where(Student.enrollment_status == status)
    if skill_level:
        query = query.where(Student.skill_level == skill_level)
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


async def update_student(db: AsyncSession, student_id: UUID, data: StudentUpdate) -> Student | None:
    """Update student fields."""
    student = await get_student_by_id(db, student_id)
    if student is None:
        return None

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(student, field, value)

    await db.commit()
    await db.refresh(student)
    return student
