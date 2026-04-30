"""attendance_service.py — batch attendance marking with tuition balance deduction.

Updated for migration 022: uses lesson_occurrence_id instead of class_session_id.
Fee is derived from the Lesson's class's tuition_fee_per_lesson.
"""

from datetime import date as date_type
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.attendance import AttendanceRecord
from app.models.lesson import Lesson
from app.models.lesson_occurrence import LessonOccurrence
from app.models.student import Student
from app.models.tuition_ledger_entry import TuitionLedgerEntry
from app.schemas.attendance import AttendanceBatchRequest


async def _upsert_ledger_entry(
    db: AsyncSession,
    student: Student,
    fee: int,
    description: str,
    attendance_record: AttendanceRecord,
    center_id: UUID,
) -> tuple[int, int]:
    """Upsert the ledger entry for this attendance, adjusting the student balance as needed."""

    expected_amount = fee if attendance_record.charge_fee else 0

    result = await db.execute(
        select(TuitionLedgerEntry).where(TuitionLedgerEntry.attendance_id == attendance_record.id)
    )
    existing_entry = result.scalar_one_or_none()

    difference = 0
    if existing_entry:
        if existing_entry.amount != expected_amount:
            difference = expected_amount - existing_entry.amount
            student.balance -= difference
            existing_entry.amount = expected_amount
            existing_entry.balance_after = student.balance
    else:
        difference = expected_amount
        student.balance -= difference

        ledger_entry = TuitionLedgerEntry(
            student_id=student.id,
            entry_type="class_fee",
            amount=expected_amount,
            balance_after=student.balance,
            attendance_id=attendance_record.id,
            entry_date=attendance_record.session_date,
            description=description,
            center_id=center_id,
        )
        db.add(ledger_entry)

    return difference, student.balance


async def mark_batch_attendance(
    db: AsyncSession, data: AttendanceBatchRequest, marked_by: UUID, center_id: UUID
) -> list[dict]:
    results = []

    # Resolve fee and description from lesson_occurrence / lesson / class (if provided)
    fee = 0
    description = str(getattr(data, "lesson_id", "") or "")[:20]
    lesson_occurrence_id = None

    if hasattr(data, "lesson_id") and data.lesson_id:
        # Try to get the occurrence record (may have been lazily created by the API layer)
        occ_result = await db.execute(
            select(LessonOccurrence).where(
                LessonOccurrence.lesson_id == data.lesson_id,
                LessonOccurrence.original_date == data.session_date,
                LessonOccurrence.center_id == center_id,
            )
        )
        occurrence = occ_result.scalar_one_or_none()
        if occurrence:
            lesson_occurrence_id = occurrence.id

        # Get lesson fee from its class
        lesson_result = await db.execute(
            select(Lesson).where(
                Lesson.id == data.lesson_id,
                Lesson.center_id == center_id,
            )
        )
        lesson = lesson_result.scalar_one_or_none()
        if lesson and lesson.class_:
            fee = lesson.class_.tuition_fee_per_lesson or 0
            description = lesson.class_.name[:50]

    elif hasattr(data, "lesson_id") and not data.lesson_id:
        # No lesson_id provided — no fee lookup possible
        description = "manual"

    for item in data.records:
        student_result = await db.execute(
            select(Student).where(
                Student.id == item.student_id,
                Student.center_id == center_id,
            ).with_for_update()
        )
        student = student_result.scalar_one_or_none()
        if not student:
            continue

        # Look up existing record via lesson_occurrence_id (new) or legacy session_date
        existing_record = None
        if lesson_occurrence_id:
            existing_res = await db.execute(
                select(AttendanceRecord).where(
                    AttendanceRecord.lesson_occurrence_id == lesson_occurrence_id,
                    AttendanceRecord.student_id == item.student_id,
                )
            )
            existing_record = existing_res.scalar_one_or_none()

        fee_deducted = 0
        balance_after = student.balance

        if existing_record:
            existing_record.status = item.status
            existing_record.charge_fee = item.charge_fee
            existing_record.notes = item.notes
            existing_record.marked_by = marked_by

            fee_deducted, balance_after = await _upsert_ledger_entry(
                db, student, fee, description, existing_record, center_id
            )
        else:
            record = AttendanceRecord(
                lesson_occurrence_id=lesson_occurrence_id,
                student_id=item.student_id,
                session_date=data.session_date,
                status=item.status,
                charge_fee=item.charge_fee,
                marked_by=marked_by,
                notes=item.notes,
                center_id=center_id,
            )
            db.add(record)
            await db.flush()

            fee_deducted, balance_after = await _upsert_ledger_entry(
                db, student, fee, description, record, center_id
            )

        results.append(
            {
                "student_id": str(item.student_id),
                "status": item.status,
                "charge_fee": item.charge_fee,
                "fee_deducted": fee_deducted,
                "balance_after": balance_after,
                "renewal_reminder_triggered": False,
            }
        )

    await db.commit()
    return results
