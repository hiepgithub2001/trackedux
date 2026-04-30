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


@router.post("/batch")
async def mark_attendance(data: AttendanceBatchRequest, db: DbSession, current_user: CurrentUser):
    """Mark attendance for a session (batch). Auto-deducts tuition balance for 'present' students.

    Lazily creates a LessonOccurrence record if one doesn't exist yet.
    """
    center_id = get_center_id(current_user)

    # Lazily create / ensure LessonOccurrence exists when lesson_id is provided
    if hasattr(data, "lesson_id") and data.lesson_id:
        lesson = await get_lesson_by_id(db, data.lesson_id, center_id)
        if lesson is not None:
            session_d = date_type.fromisoformat(str(data.session_date)) if isinstance(data.session_date, str) else data.session_date
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
        select(AttendanceRecord).where(
            AttendanceRecord.lesson_occurrence_id == occ.id,
            AttendanceRecord.center_id == center_id,
        )
    )
    records = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "student_id": str(r.student_id),
            "student_name": r.student.name if r.student else "",
            "status": r.status,
            "charge_fee": r.charge_fee,
            "notes": r.notes,
        }
        for r in records
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
