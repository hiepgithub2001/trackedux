"""Lessons API routes — lesson CRUD and per-occurrence overrides."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, HTTPException, status

from app.core.deps import CurrentUser, DbSession, get_center_id
from app.crud.lesson import (
    create_lesson,
    deactivate_lesson,
    get_lesson_by_id,
    get_occurrence,
    list_lessons,
    update_lesson_series,
    upsert_occurrence,
)
from app.schemas.lesson import (
    LessonCreate,
    LessonResponse,
    LessonSeriesUpdate,
    OccurrenceOverrideRequest,
    OccurrenceResponse,
)
from app.services.recurrence_service import parse_rrule_day
from app.services.schedule_service import check_scheduling_conflicts

router = APIRouter(prefix="/lessons", tags=["Lessons"])


def _lesson_to_response(lesson) -> LessonResponse:
    return LessonResponse(
        id=lesson.id,
        class_id=lesson.class_id,
        class_name=lesson.class_.name if lesson.class_ else None,
        teacher_id=lesson.teacher_id,
        teacher_name=lesson.teacher.full_name if lesson.teacher else None,
        title=lesson.title,
        start_time=lesson.start_time.strftime("%H:%M"),
        duration_minutes=lesson.duration_minutes,
        day_of_week=lesson.day_of_week,
        specific_date=lesson.specific_date,
        rrule=lesson.rrule,
        is_active=lesson.is_active,
        created_at=lesson.created_at,
        updated_at=lesson.updated_at,
    )


@router.get("", response_model=list[LessonResponse])
async def get_lessons(
    db: DbSession,
    current_user: CurrentUser,
    class_id: UUID | None = None,
    teacher_id: UUID | None = None,
    is_active: bool = True,
):
    """List lessons for the current center."""
    center_id = get_center_id(current_user)
    lessons = await list_lessons(db, center_id=center_id, class_id=class_id, teacher_id=teacher_id, is_active=is_active)
    return [_lesson_to_response(lesson) for lesson in lessons]


@router.get("/{lesson_id}", response_model=LessonResponse)
async def get_lesson(lesson_id: UUID, db: DbSession, current_user: CurrentUser):
    """Get lesson detail."""
    center_id = get_center_id(current_user)
    lesson = await get_lesson_by_id(db, lesson_id, center_id)
    if lesson is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    return _lesson_to_response(lesson)


@router.post("", response_model=LessonResponse, status_code=status.HTTP_201_CREATED)
async def create_lesson_endpoint(data: LessonCreate, db: DbSession, current_user: CurrentUser):
    """Create a lesson (one-off or recurring). Admin only. Returns 409 on scheduling conflict."""
    if current_user.role not in ("admin", "superadmin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    center_id = get_center_id(current_user)

    # Determine day_of_week for conflict checking
    day_of_week: int | None = None
    if data.rrule:
        day_of_week = parse_rrule_day(data.rrule)

    # Get enrolled students if class is attached
    student_ids: list[UUID] = []
    if data.class_id:

        from app.crud.class_ import get_class_by_id
        cls = await get_class_by_id(db, data.class_id, center_id)
        if cls is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
        student_ids = [e.student_id for e in (cls.enrollments or []) if e.is_active]

    if day_of_week is not None:
        conflicts = await check_scheduling_conflicts(
            db,
            data.teacher_id,
            day_of_week,
            data.start_time,
            data.duration_minutes,
            student_ids,
            center_id=center_id,
        )
        if conflicts:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"message": "Scheduling conflict", "conflicts": conflicts},
            )

    lesson = await create_lesson(db, data, center_id)
    lesson = await get_lesson_by_id(db, lesson.id, center_id)
    return _lesson_to_response(lesson)


@router.patch("/{lesson_id}", response_model=LessonResponse)
async def update_lesson_series_endpoint(
    lesson_id: UUID, data: LessonSeriesUpdate, db: DbSession, current_user: CurrentUser
):
    """Edit the recurring series (time, rrule, title). Admin only.
    Does NOT touch any persisted LessonOccurrence records.
    """
    if current_user.role not in ("admin", "superadmin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    center_id = get_center_id(current_user)

    lesson = await update_lesson_series(db, lesson_id, data, center_id)
    if lesson is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    return _lesson_to_response(lesson)


@router.delete("/{lesson_id}")
async def delete_lesson_endpoint(lesson_id: UUID, db: DbSession, current_user: CurrentUser):
    """Soft-delete a lesson. Admin only."""
    if current_user.role not in ("admin", "superadmin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    center_id = get_center_id(current_user)
    success = await deactivate_lesson(db, lesson_id, center_id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")
    return {"detail": "Lesson deactivated"}


# ─── Per-Occurrence Override Endpoints ──────────────────────────────────────

@router.get("/{lesson_id}/occurrences/{original_date}", response_model=OccurrenceResponse)
async def get_occurrence_endpoint(
    lesson_id: UUID, original_date: str, db: DbSession, current_user: CurrentUser
):
    """Get the override record for a single occurrence. 404 if still virtual."""
    center_id = get_center_id(current_user)
    occ_date = date.fromisoformat(original_date)
    occ = await get_occurrence(db, lesson_id, occ_date, center_id)
    if occ is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No override record (occurrence is virtual/active)",
        )
    return OccurrenceResponse(
        id=occ.id,
        lesson_id=occ.lesson_id,
        original_date=occ.original_date,
        status=occ.status,
        override_date=occ.override_date,
        override_start_time=occ.override_start_time.strftime("%H:%M") if occ.override_start_time else None,
        center_id=occ.center_id,
    )


@router.patch("/{lesson_id}/occurrences/{original_date}", response_model=OccurrenceResponse)
async def override_occurrence_endpoint(
    lesson_id: UUID,
    original_date: str,
    data: OccurrenceOverrideRequest,
    db: DbSession,
    current_user: CurrentUser,
):
    """Cancel, reschedule, or revert a single occurrence. Admin only."""
    if current_user.role not in ("admin", "superadmin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin access required")
    center_id = get_center_id(current_user)

    lesson = await get_lesson_by_id(db, lesson_id, center_id)
    if lesson is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lesson not found")

    occ_date = date.fromisoformat(original_date)

    # Conflict check for reschedule
    if data.action == "reschedule" and data.override_date is not None:
        override_start = data.override_start_time or lesson.start_time.strftime("%H:%M")
        # day_of_week derived from override_date
        override_dow = data.override_date.weekday()
        conflicts = await check_scheduling_conflicts(
            db,
            lesson.teacher_id,
            override_dow,
            override_start,
            lesson.duration_minutes,
            [],
            exclude_lesson_id=lesson_id,
            center_id=center_id,
        )
        if conflicts:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"message": "Scheduling conflict on reschedule", "conflicts": conflicts},
            )

    occ = await upsert_occurrence(db, lesson_id, occ_date, data, center_id)
    return OccurrenceResponse(
        id=occ.id,
        lesson_id=occ.lesson_id,
        original_date=occ.original_date,
        status=occ.status,
        override_date=occ.override_date,
        override_start_time=occ.override_start_time.strftime("%H:%M") if occ.override_start_time else None,
        center_id=occ.center_id,
    )
