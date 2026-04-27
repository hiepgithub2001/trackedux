"""Attendance API routes."""
from uuid import UUID

from fastapi import APIRouter
from sqlalchemy import select

from app.core.deps import CurrentUser, DbSession
from app.models.attendance import AttendanceRecord
from app.schemas.attendance import AttendanceBatchRequest
from app.services.attendance_service import mark_batch_attendance

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.post("/batch")
async def mark_attendance(data: AttendanceBatchRequest, db: DbSession, current_user: CurrentUser):
    """Mark attendance for a session (batch). Auto-deducts package sessions."""
    results = await mark_batch_attendance(db, data, current_user.id)
    return {"records": results}


@router.get("/session/{class_session_id}/{session_date}")
async def get_session_attendance(class_session_id: UUID, session_date: str, db: DbSession, current_user: CurrentUser):
    """Get attendance records for a specific session on a given date."""
    from datetime import date as date_type
    d = date_type.fromisoformat(session_date)
    result = await db.execute(
        select(AttendanceRecord).where(AttendanceRecord.class_session_id == class_session_id, AttendanceRecord.session_date == d)
    )
    records = result.scalars().all()
    return [{"id": str(r.id), "student_id": str(r.student_id), "student_name": r.student.name if r.student else "",
             "status": r.status, "notes": r.notes} for r in records]


@router.get("/student/{student_id}")
async def get_student_attendance(student_id: UUID, db: DbSession, current_user: CurrentUser):
    """Get attendance history for a student."""
    result = await db.execute(
        select(AttendanceRecord).where(AttendanceRecord.student_id == student_id).order_by(AttendanceRecord.session_date.desc())
    )
    records = result.scalars().all()
    return [{"id": str(r.id), "session_date": r.session_date.isoformat(), "status": r.status, "notes": r.notes} for r in records]
