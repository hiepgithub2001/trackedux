"""Teacher API routes."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.core.deps import CurrentUser, DbSession, get_center_id
from app.crud.teacher import create_teacher, get_teacher_by_id, list_teachers, replace_availability, update_teacher
from app.schemas.teacher import AvailabilityUpdate, TeacherCreate, TeacherResponse, TeacherUpdate

router = APIRouter(prefix="/teachers", tags=["Teachers"])


def _teacher_to_response(teacher) -> dict:
    """Convert teacher model to response dict with formatted availability."""
    return TeacherResponse(
        id=teacher.id,
        full_name=teacher.full_name,
        phone=teacher.phone,
        email=teacher.email,
        notes=teacher.notes,
        color=teacher.color,
        is_active=teacher.is_active,
        availability=[
            {
                "day_of_week": a.day_of_week,
                "start_time": a.start_time.strftime("%H:%M"),
                "end_time": a.end_time.strftime("%H:%M"),
            }
            for a in (teacher.availability or [])
        ],
        created_at=teacher.created_at,
        updated_at=teacher.updated_at,
    )


@router.get("", response_model=list[TeacherResponse])
async def get_teachers(db: DbSession, current_user: CurrentUser):
    """List all teachers. Admin and Staff."""
    if current_user.role not in ("admin", "staff"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    center_id = get_center_id(current_user)
    teachers = await list_teachers(db, center_id=center_id)
    return [_teacher_to_response(t) for t in teachers]


@router.get("/{teacher_id}", response_model=TeacherResponse)
async def get_teacher(teacher_id: UUID, db: DbSession, current_user: CurrentUser):
    """Get teacher detail with availability."""
    if current_user.role not in ("admin", "staff"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    center_id = get_center_id(current_user)
    teacher = await get_teacher_by_id(db, teacher_id, center_id)
    if teacher is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")
    return _teacher_to_response(teacher)


@router.post("", response_model=TeacherResponse, status_code=status.HTTP_201_CREATED)
async def create_teacher_endpoint(data: TeacherCreate, db: DbSession, current_user: CurrentUser):
    """Create a new teacher. Admin only."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    center_id = get_center_id(current_user)
    teacher = await create_teacher(db, data, center_id)
    return _teacher_to_response(teacher)


@router.patch("/{teacher_id}", response_model=TeacherResponse)
async def update_teacher_endpoint(teacher_id: UUID, data: TeacherUpdate, db: DbSession, current_user: CurrentUser):
    """Update teacher fields. Admin only."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    center_id = get_center_id(current_user)
    teacher = await update_teacher(db, teacher_id, data, center_id)
    if teacher is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")
    return _teacher_to_response(teacher)


@router.put("/{teacher_id}/availability", response_model=TeacherResponse)
async def set_availability(teacher_id: UUID, data: AvailabilityUpdate, db: DbSession, current_user: CurrentUser):
    """Replace all availability slots. Admin only."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    center_id = get_center_id(current_user)
    teacher = await replace_availability(db, teacher_id, data.slots, center_id)
    if teacher is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Teacher not found")
    return _teacher_to_response(teacher)
