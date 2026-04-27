"""Student API routes."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.core.deps import CurrentUser, DbSession
from app.crud.student import create_student, get_student_by_id, list_students, update_student
from app.schemas.student import (
    PaginatedStudents,
    StudentCreate,
    StudentListItem,
    StudentResponse,
    StudentStatusChange,
    StudentUpdate,
)
from app.services.student_service import change_student_status

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("", response_model=PaginatedStudents)
async def get_students(
    db: DbSession,
    current_user: CurrentUser,
    status_filter: str | None = Query(None, alias="status"),
    skill_level: str | None = None,
    search: str | None = None,
    sort_by: str = "name",
    sort_order: str = "asc",
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """List students with filters, search, sort, and pagination."""
    students, total = await list_students(
        db,
        status=status_filter,
        skill_level=skill_level,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
        page=page,
        page_size=page_size,
    )

    items = []
    for s in students:
        items.append(
            StudentListItem(
                id=s.id,
                name=s.name,
                nickname=s.nickname,
                age=s.age,
                skill_level=s.skill_level,
                enrollment_status=s.enrollment_status,
                enrolled_at=s.enrolled_at,
                contact_name=(s.contact or {}).get("name") if s.contact else None,
            )
        )

    return PaginatedStudents(items=items, total=total, page=page, page_size=page_size)


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(student_id: UUID, db: DbSession, current_user: CurrentUser):
    """Get student detail. Staff cannot see parent contact info."""
    student = await get_student_by_id(db, student_id)
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    response = StudentResponse.model_validate(student)
    return response


@router.post("", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_student_endpoint(data: StudentCreate, db: DbSession, current_user: CurrentUser):
    """Create a new student. Admin and Staff."""
    if current_user.role not in ("admin", "staff"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    student = await create_student(db, data)
    return StudentResponse.model_validate(student)


@router.patch("/{student_id}", response_model=StudentResponse)
async def update_student_endpoint(
    student_id: UUID, data: StudentUpdate, db: DbSession, current_user: CurrentUser
):
    """Update student fields. Admin and Staff."""
    if current_user.role not in ("admin", "staff"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    student = await update_student(db, student_id, data)
    if student is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return StudentResponse.model_validate(student)


@router.patch("/{student_id}/status", response_model=StudentResponse)
async def change_status(
    student_id: UUID, data: StudentStatusChange, db: DbSession, current_user: CurrentUser
):
    """Change enrollment status. Admin only. Creates audit trail."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    await change_student_status(
        db, student_id, data.status, current_user.id, data.reason
    )

    student = await get_student_by_id(db, student_id)
    return StudentResponse.model_validate(student)
