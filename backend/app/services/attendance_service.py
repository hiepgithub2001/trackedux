"""Attendance service — batch marking, package session deduction."""
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.attendance import AttendanceRecord
from app.models.package import Package
from app.schemas.attendance import AttendanceBatchRequest


async def mark_batch_attendance(db: AsyncSession, data: AttendanceBatchRequest, marked_by: UUID) -> list[dict]:
    results = []
    for item in data.records:
        # Get active package for student
        pkg_result = await db.execute(select(Package).where(Package.student_id == item.student_id, Package.is_active == True))
        active_pkg = pkg_result.scalar_one_or_none()

        record = AttendanceRecord(
            class_session_id=data.class_session_id, student_id=item.student_id,
            package_id=active_pkg.id if active_pkg else None, session_date=data.session_date,
            status=item.status, marked_by=marked_by, notes=item.notes,
        )
        db.add(record)

        renewal_triggered = False
        remaining = None

        if item.status == "present" and active_pkg:
            active_pkg.remaining_sessions -= 1
            remaining = active_pkg.remaining_sessions
            if active_pkg.remaining_sessions <= 2 and active_pkg.reminder_status == "none":
                active_pkg.reminder_status = "reminded_once"
                renewal_triggered = True

        results.append({
            "student_id": str(item.student_id), "status": item.status,
            "package_remaining": remaining, "renewal_reminder_triggered": renewal_triggered,
        })

    await db.commit()
    return results
