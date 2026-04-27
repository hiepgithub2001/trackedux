"""Class API routes."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.core.deps import CurrentUser, DbSession
from app.crud.class_session import (
    create_class_session,
    enroll_student,
    get_class_session_by_id,
    list_class_sessions,
    unenroll_student,
)
from app.schemas.class_session import (
    ClassSessionCreate,
    ClassSessionResponse,
    EnrollRequest,
    _derive_end_time,
)
from app.services.schedule_service import check_scheduling_conflicts

router = APIRouter(prefix="/classes", tags=["Classes"])


def _class_to_response(cs) -> ClassSessionResponse:
    """Convert class session model to response, with derived end_time."""
    start_str = cs.start_time.strftime("%H:%M")
    return ClassSessionResponse(
        id=cs.id,
        teacher_id=cs.teacher_id,
        name=cs.name,
        day_of_week=cs.day_of_week,
        start_time=start_str,
        duration_minutes=cs.duration_minutes,
        end_time=_derive_end_time(start_str, cs.duration_minutes),
        is_recurring=cs.is_recurring,
        is_makeup=cs.is_makeup,
        is_active=cs.is_active,
        teacher_name=cs.teacher.full_name if cs.teacher else None,
        enrolled_students=[
            {"id": str(e.student_id), "name": e.student.name if e.student else ""}
            for e in (cs.enrollments or [])
            if e.is_active
        ],
        created_at=cs.created_at,
        updated_at=cs.updated_at,
    )


@router.get("", response_model=list[ClassSessionResponse])
async def get_classes(
    db: DbSession,
    current_user: CurrentUser,
    teacher_id: UUID | None = None,
    day_of_week: int | None = Query(None, ge=0, le=6),
    is_active: bool = True,
):
    """List class sessions with filters."""
    classes = await list_class_sessions(db, teacher_id, day_of_week, is_active)
    return [_class_to_response(c) for c in classes]


@router.get("/{class_id}", response_model=ClassSessionResponse)
async def get_class(class_id: UUID, db: DbSession, current_user: CurrentUser):
    """Get class detail with enrolled students."""
    cs = await get_class_session_by_id(db, class_id)
    if cs is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    return _class_to_response(cs)


@router.post("", response_model=ClassSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_class(data: ClassSessionCreate, db: DbSession, current_user: CurrentUser):
    """Create a class session. Admin only. Returns 409 on scheduling conflict."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    conflicts = await check_scheduling_conflicts(
        db,
        data.teacher_id,
        data.day_of_week,
        data.start_time,
        data.duration_minutes,
        data.student_ids,
    )
    if conflicts:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "Scheduling conflict", "conflicts": conflicts},
        )

    cs = await create_class_session(db, data)
    cs = await get_class_session_by_id(db, cs.id)  # Reload with relationships
    return _class_to_response(cs)


@router.post("/{class_id}/enroll")
async def enroll_student_endpoint(class_id: UUID, data: EnrollRequest, db: DbSession, current_user: CurrentUser):
    """Add student to class. Admin only. Returns 409 only on time-overlap conflict."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")

    cs = await get_class_session_by_id(db, class_id)
    if cs is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

    # No max-capacity check (clarification 2026-04-27).
    conflicts = await check_scheduling_conflicts(
        db,
        cs.teacher_id,
        cs.day_of_week,
        cs.start_time.strftime("%H:%M"),
        cs.duration_minutes,
        [data.student_id],
        exclude_class_id=class_id,
    )
    student_conflicts = [c for c in conflicts if c["type"] == "student"]
    if student_conflicts:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "Student scheduling conflict", "conflicts": student_conflicts},
        )

    await enroll_student(db, class_id, data.student_id)
    return {"detail": "Student enrolled"}


@router.delete("/{class_id}/enroll/{student_id}")
async def unenroll_student_endpoint(class_id: UUID, student_id: UUID, db: DbSession, current_user: CurrentUser):
    """Remove student from class. Admin only."""
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    success = await unenroll_student(db, class_id, student_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")
    return {"detail": "Student unenrolled"}
