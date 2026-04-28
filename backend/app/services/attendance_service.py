"""Attendance service — batch marking with tuition balance deduction."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import AttendanceRecord
from app.models.class_session import ClassSession
from app.models.student import Student
from app.models.tuition_ledger_entry import TuitionLedgerEntry
from app.schemas.attendance import AttendanceBatchRequest


async def _deduct_class_fee(
    db: AsyncSession,
    student: Student,
    class_session: ClassSession,
    attendance_record: AttendanceRecord,
    center_id: UUID,
) -> tuple[int, int]:
    """Deduct class fee from student balance. Returns (fee_deducted, balance_after)."""
    fee = class_session.tuition_fee_per_lesson
    if not fee or fee <= 0:
        return 0, student.balance

    student.balance -= fee

    # Get display_id for ledger description
    display_id = class_session.display_id if hasattr(class_session, "display_id") else str(class_session.id)[:8]

    ledger_entry = TuitionLedgerEntry(
        student_id=student.id,
        entry_type="class_fee",
        amount=fee,
        balance_after=student.balance,
        attendance_id=attendance_record.id,
        class_session_id=class_session.id,
        entry_date=attendance_record.session_date,
        description=display_id,
        center_id=center_id,
    )
    db.add(ledger_entry)
    return fee, student.balance


async def _reverse_class_fee(
    db: AsyncSession,
    student: Student,
    class_session: ClassSession,
    attendance_record: AttendanceRecord,
    center_id: UUID,
) -> tuple[int, int]:
    """Reverse a previous class fee deduction. Returns (fee_reversed, balance_after)."""
    fee = class_session.tuition_fee_per_lesson
    if not fee or fee <= 0:
        return 0, student.balance

    # Find and delete the existing ledger entry for this attendance
    result = await db.execute(
        select(TuitionLedgerEntry).where(TuitionLedgerEntry.attendance_id == attendance_record.id)
    )
    existing_entry = result.scalar_one_or_none()

    if existing_entry:
        # Restore the balance
        student.balance += existing_entry.amount
        await db.delete(existing_entry)

    return fee, student.balance


async def mark_batch_attendance(
    db: AsyncSession, data: AttendanceBatchRequest, marked_by: UUID, center_id: UUID
) -> list[dict]:
    results = []

    # Fetch the class session to get tuition_fee_per_lesson
    cs_result = await db.execute(
        select(ClassSession).where(ClassSession.id == data.class_session_id)
    )
    class_session = cs_result.scalar_one_or_none()

    for item in data.records:
        # Fetch student with lock for atomic balance update
        student_result = await db.execute(
            select(Student).where(
                Student.id == item.student_id,
                Student.center_id == center_id,
            ).with_for_update()
        )
        student = student_result.scalar_one_or_none()
        if not student:
            continue

        # Check for existing attendance record
        existing_res = await db.execute(
            select(AttendanceRecord).where(
                AttendanceRecord.class_session_id == data.class_session_id,
                AttendanceRecord.student_id == item.student_id,
                AttendanceRecord.session_date == data.session_date,
            )
        )
        existing_record = existing_res.scalar_one_or_none()

        fee_deducted = 0
        balance_after = student.balance

        if existing_record:
            old_status = existing_record.status
            new_status = item.status

            existing_record.status = new_status
            existing_record.notes = item.notes
            existing_record.marked_by = marked_by

            if class_session:
                if old_status == "present" and new_status != "present":
                    # Reverse deduction
                    fee_deducted, balance_after = await _reverse_class_fee(
                        db, student, class_session, existing_record, center_id
                    )
                    fee_deducted = 0  # reversal, not a new deduction
                elif old_status != "present" and new_status == "present":
                    # Apply deduction
                    fee_deducted, balance_after = await _deduct_class_fee(
                        db, student, class_session, existing_record, center_id
                    )
        else:
            record = AttendanceRecord(
                class_session_id=data.class_session_id,
                student_id=item.student_id,
                session_date=data.session_date,
                status=item.status,
                marked_by=marked_by,
                notes=item.notes,
                center_id=center_id,
            )
            db.add(record)
            await db.flush()  # get record.id for ledger entry FK

            if item.status == "present" and class_session:
                fee_deducted, balance_after = await _deduct_class_fee(
                    db, student, class_session, record, center_id
                )

        results.append(
            {
                "student_id": str(item.student_id),
                "status": item.status,
                "fee_deducted": fee_deducted,
                "balance_after": balance_after,
                "renewal_reminder_triggered": False,
            }
        )

    await db.commit()
    return results
