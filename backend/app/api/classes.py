"""Class API routes — cohort management (replaces ClassSession CRUD)."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.core.deps import CurrentUser, DbSession, get_center_id
from app.crud.class_ import (
    create_class,
    deactivate_class,
    enroll_student,
    get_class_by_id,
    list_classes,
    unenroll_student,
    update_class,
)
from app.schemas.class_ import (
    ClassCreate,
    ClassEnrollRequest,
    ClassResponse,
    ClassUpdate,
    EnrolledStudent,
)
from app.services.schedule_service import check_scheduling_conflicts

router = APIRouter(prefix="/classes", tags=["Classes"])


def _class_to_response(cls, current_user) -> ClassResponse:
    """Convert Class ORM object to ClassResponse with role-based fee visibility."""
    fee = cls.tuition_fee_per_lesson if current_user.role in ("admin", "superadmin") else None

    active_enrollments = [
        EnrolledStudent(id=e.student_id, name=e.student.name if e.student else "")
        for e in (cls.enrollments or [])
        if e.is_active
    ]

    return ClassResponse(
        id=cls.id,
        name=cls.name,
        teacher_id=cls.teacher_id,
        teacher_name=cls.teacher.full_name if cls.teacher else None,
        tuition_fee_per_lesson=fee,
        lesson_kind_id=cls.lesson_kind_id,
        lesson_kind_name=cls.lesson_kind.name if cls.lesson_kind else None,
        is_active=cls.is_active,
        enrolled_count=len(active_enrollments),
        enrolled_students=active_enrollments,
        created_at=cls.created_at,
        updated_at=cls.updated_at,
    )


@router.get("", response_model=list[ClassResponse])
async def get_classes(
    db: DbSession,
    current_user: CurrentUser,
    teacher_id: UUID | None = None,
    is_active: bool = True,
):
    """List classes for the current center."""
    center_id = get_center_id(current_user)
    classes = await list_classes(db, center_id=center_id, teacher_id=teacher_id, is_active=is_active)
    return [_class_to_response(c, current_user) for c in classes]


@router.get("/{class_id}", response_model=ClassResponse)
async def get_class(class_id: UUID, db: DbSession, current_user: CurrentUser):
    """Get class detail with enrolled students."""
    center_id = get_center_id(current_user)
    cls = await get_class_by_id(db, class_id, center_id)
    if cls is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    return _class_to_response(cls, current_user)


@router.post("", response_model=ClassResponse, status_code=status.HTTP_201_CREATED)
async def create_class_endpoint(data: ClassCreate, db: DbSession, current_user: CurrentUser):
    """Create a class. Admin only."""
    if current_user.role not in ("admin", "superadmin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    center_id = get_center_id(current_user)
    cls = await create_class(db, data, center_id)
    cls = await get_class_by_id(db, cls.id, center_id)
    return _class_to_response(cls, current_user)


@router.put("/{class_id}", response_model=ClassResponse)
async def update_class_endpoint(class_id: UUID, data: ClassUpdate, db: DbSession, current_user: CurrentUser):
    """Update a class. Admin only."""
    if current_user.role not in ("admin", "superadmin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    center_id = get_center_id(current_user)
    cls = await update_class(db, class_id, data, center_id)
    if cls is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    return _class_to_response(cls, current_user)


@router.delete("/{class_id}")
async def delete_class_endpoint(class_id: UUID, db: DbSession, current_user: CurrentUser):
    """Soft-delete a class (is_active=false). Admin only."""
    if current_user.role not in ("admin", "superadmin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    center_id = get_center_id(current_user)
    success = await deactivate_class(db, class_id, center_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    return {"detail": "Class deactivated"}


@router.post("/{class_id}/enroll")
async def enroll_student_endpoint(
    class_id: UUID, data: ClassEnrollRequest, db: DbSession, current_user: CurrentUser
):
    """Enroll a student in a class. Admin only. Returns 409 on scheduling conflict."""
    if current_user.role not in ("admin", "superadmin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    center_id = get_center_id(current_user)

    cls = await get_class_by_id(db, class_id, center_id)
    if cls is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")

    # Check conflicts for each lesson attached to this class
    from app.crud.lesson import list_lessons
    lessons = await list_lessons(db, center_id=center_id, class_id=class_id, is_active=True)
    for lesson in lessons:
        if lesson.day_of_week is not None:
            conflicts = await check_scheduling_conflicts(
                db,
                lesson.teacher_id,
                lesson.day_of_week,
                lesson.start_time.strftime("%H:%M"),
                lesson.duration_minutes,
                [data.student_id],
                exclude_lesson_id=lesson.id,
                center_id=center_id,
            )
            student_conflicts = [c for c in conflicts if c["type"] == "student"]
            if student_conflicts:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"message": "Student scheduling conflict", "conflicts": student_conflicts},
                )

    enrolled_since: date | None = None
    if data.enrolled_since:
        from datetime import date as date_type
        enrolled_since = date_type.fromisoformat(data.enrolled_since)

    await enroll_student(db, class_id, data.student_id, center_id, enrolled_since)
    return {"detail": "Student enrolled"}


@router.delete("/{class_id}/enroll/{student_id}")
async def unenroll_student_endpoint(
    class_id: UUID,
    student_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
    unenrolled_at: str | None = Query(None),
):
    """Remove student from a class. Admin only."""
    if current_user.role not in ("admin", "superadmin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    center_id = get_center_id(current_user)

    unenrolled_at_date: date | None = None
    if unenrolled_at:
        from datetime import date as date_type
        unenrolled_at_date = date_type.fromisoformat(unenrolled_at)

    success = await unenroll_student(db, class_id, student_id, center_id, unenrolled_at_date)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")
    return {"detail": "Student unenrolled"}
