"""Attendance API routes — updated to use lesson_id + LessonOccurrence lazy creation."""

from datetime import date as date_type
from uuid import UUID

from fastapi import APIRouter
from sqlalchemy import select

from app.core.deps import CurrentUser, DbSession, get_center_id
from app.crud.lesson import get_lesson_by_id, get_occurrence, upsert_occurrence
from app.models.attendance import AttendanceRecord
from app.schemas.attendance import AttendanceBatchRequest
from app.schemas.lesson import OccurrenceOverrideRequest
from app.services.attendance_service import mark_batch_attendance

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.get("/weekly")
async def get_weekly_attendance(
    db: DbSession,
    current_user: CurrentUser,
    week_start: date_type | None = None,
    teacher_id: UUID | None = None,
):
    """Get weekly attendance view data using the unified read model.

    Materializes occurrences on the fly for the requested week.
    """
    from datetime import timedelta

    from sqlalchemy import func

    from app.api.schedule import _build_session_dicts
    from app.crud.lesson import bulk_upsert_occurrences, list_lessons
    from app.models.lesson_occurrence import LessonOccurrence
    from app.services.recurrence_service import _build_occurrence

    center_id = get_center_id(current_user)
    today = date_type.today()

    if week_start is None:
        week_start = today - timedelta(days=today.weekday())  # Monday
    week_end = week_start + timedelta(days=6)

    # 1. Load all lessons (active & inactive) so lesson_map is complete
    lessons = await list_lessons(db, center_id=center_id, teacher_id=teacher_id, is_active=None)
    if not lessons:
        return {"week_start": week_start.isoformat(), "week_end": week_end.isoformat(), "sessions": []}

    lesson_map = {str(lesson.id): lesson for lesson in lessons}

    # 2. Materialize rows for active lessons for the requested week
    active_lessons = [lesson_obj for lesson_obj in lessons if lesson_obj.is_active]
    inserted = await bulk_upsert_occurrences(db, active_lessons, week_start, week_end, center_id)
    if inserted > 0:
        await db.commit()

    # 3. Apply unified read model: fetch from DB
    result = await db.execute(
        select(LessonOccurrence).where(
            LessonOccurrence.lesson_id.in_([lesson_obj.id for lesson_obj in lessons]),
            LessonOccurrence.center_id == center_id,
            func.coalesce(LessonOccurrence.override_date, LessonOccurrence.original_date) >= week_start,
            func.coalesce(LessonOccurrence.override_date, LessonOccurrence.original_date) <= week_end,
        )
    )
    occ_rows = result.scalars().all()

    virtual_occs = []
    for occ_row in occ_rows:
        lesson = lesson_map.get(str(occ_row.lesson_id))
        if not lesson:
            continue

        effective_date = occ_row.override_date if occ_row.override_date else occ_row.original_date

        # Unified read model filter:
        # Past portion: keep all (even inactive)
        # Future portion: keep only active
        if effective_date >= today and not lesson.is_active:
            continue

        class_name = lesson.class_.name if lesson.class_ else None
        display_name = lesson.title or class_name or ""
        teacher_id_str = str(lesson.teacher_id)

        v_occ = _build_occurrence(
            lesson, str(lesson.id), class_name, display_name, teacher_id_str, occ_row.original_date, occ_row
        )
        virtual_occs.append(v_occ)

    sessions = await _build_session_dicts(db, virtual_occs, lesson_map, center_id)

    return {
        "week_start": week_start.isoformat(),
        "week_end": week_end.isoformat(),
        "sessions": sessions,
    }


@router.post("/batch")
async def mark_attendance(data: AttendanceBatchRequest, db: DbSession, current_user: CurrentUser):
    """Mark attendance for a session (batch). Auto-deducts tuition balance for 'present' students.

    Lazily creates a LessonOccurrence record if one doesn't exist yet.
    """
    center_id = get_center_id(current_user)

    # Lazily create / ensure LessonOccurrence exists when lesson_id is provided
    if data.lesson_id:
        lesson = await get_lesson_by_id(db, data.lesson_id, center_id)
        if lesson is not None:
            session_d = (
                date_type.fromisoformat(str(data.session_date))
                if isinstance(data.session_date, str)
                else data.session_date
            )
            existing = await get_occurrence(db, data.lesson_id, session_d, center_id)
            if existing is None:
                # Materialize the occurrence record lazily
                await upsert_occurrence(
                    db,
                    data.lesson_id,
                    session_d,
                    OccurrenceOverrideRequest(action="revert"),
                    center_id,
                )

    results = await mark_batch_attendance(db, data, current_user.id, center_id)

    # Hide financial details for non-admin roles (FR-025)
    is_admin = current_user.role in ("admin", "superadmin")
    for r in results:
        if not is_admin:
            r["balance_after"] = None
            r["fee_deducted"] = None
        r.pop("package_remaining", None)

    return {"records": results}


@router.get("/session/{lesson_id}/{session_date}")
async def get_session_attendance(
    lesson_id: UUID,
    session_date: str,
    db: DbSession,
    current_user: CurrentUser,
):
    """Get attendance for a lesson occurrence on a given date, scoped to center."""
    center_id = get_center_id(current_user)
    d = date_type.fromisoformat(session_date)

    # Query via lesson_occurrence_id
    occ = await get_occurrence(db, lesson_id, d, center_id)
    if occ is None:
        return []

    result = await db.execute(
        select(AttendanceRecord)
        .where(
            AttendanceRecord.lesson_occurrence_id == occ.id,
            AttendanceRecord.center_id == center_id,
        )
        .order_by(AttendanceRecord.created_at.desc())
    )
    records = result.scalars().all()

    # Deduplicate: keep the newest record per student (handles legacy duplicate rows)
    seen: set = set()
    deduped = []
    for r in records:
        if r.student_id not in seen:
            seen.add(r.student_id)
            deduped.append(r)

    return [
        {
            "id": str(r.id),
            "student_id": str(r.student_id),
            "student_name": r.student.name if r.student else "",
            "status": r.status,
            "charge_fee": r.charge_fee,
            "notes": r.notes,
        }
        for r in deduped
    ]


@router.get("/student/{student_id}")
async def get_student_attendance(student_id: UUID, db: DbSession, current_user: CurrentUser):
    """Get attendance history for a student, scoped to center."""
    center_id = get_center_id(current_user)
    result = await db.execute(
        select(AttendanceRecord)
        .where(
            AttendanceRecord.student_id == student_id,
            AttendanceRecord.center_id == center_id,
        )
        .order_by(AttendanceRecord.session_date.desc())
    )
    records = result.scalars().all()
    return [
        {"id": str(r.id), "session_date": r.session_date.isoformat(), "status": r.status, "notes": r.notes}
        for r in records
    ]
