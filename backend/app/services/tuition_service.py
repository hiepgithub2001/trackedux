"""Tuition service — payment recording, balance computation, ledger queries."""

from datetime import date
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.student import Student
from app.models.tuition_ledger_entry import TuitionLedgerEntry
from app.models.tuition_payment import TuitionPayment
from app.schemas.tuition import (
    LedgerEntryResponse,
    StudentBalanceResponse,
    StudentLedgerResponse,
    TuitionPaymentCreate,
    TuitionPaymentResponse,
)


async def record_payment(
    db: AsyncSession,
    data: TuitionPaymentCreate,
    recorded_by: UUID,
    center_id: UUID,
) -> TuitionPaymentResponse:
    """Record a tuition payment, create ledger entry, update student balance."""
    # Fetch the student (with lock for atomic balance update)
    result = await db.execute(
        select(Student).where(Student.id == data.student_id, Student.center_id == center_id).with_for_update()
    )
    student = result.scalar_one_or_none()
    if not student:
        raise ValueError(f"Student {data.student_id} not found in this center")

    payment_date = data.payment_date or date.today()

    # Create TuitionPayment record
    payment = TuitionPayment(
        student_id=data.student_id,
        amount=data.amount,
        payment_date=payment_date,
        payment_method=data.payment_method,
        notes=data.notes,
        recorded_by=recorded_by,
        center_id=center_id,
    )
    db.add(payment)
    await db.flush()  # get payment.id

    # Update cached balance
    student.balance += data.amount
    new_balance = student.balance

    # Create ledger entry
    description = f"Payment - {data.payment_method}" if data.payment_method else "Payment"
    ledger_entry = TuitionLedgerEntry(
        student_id=data.student_id,
        entry_type="payment",
        amount=data.amount,
        balance_after=new_balance,
        payment_id=payment.id,
        entry_date=payment_date,
        description=description,
        center_id=center_id,
    )
    db.add(ledger_entry)
    await db.commit()
    await db.refresh(payment)

    return TuitionPaymentResponse(
        id=payment.id,
        student_id=payment.student_id,
        student_name=student.name,
        amount=payment.amount,
        payment_date=payment.payment_date,
        payment_method=payment.payment_method,
        notes=payment.notes,
        recorded_by=payment.recorded_by,
        balance_after=new_balance,
        created_at=payment.created_at,
    )


async def list_payments(
    db: AsyncSession,
    center_id: UUID,
    student_id: UUID | None = None,
    from_date: date | None = None,
    to_date: date | None = None,
) -> list[dict]:
    """List tuition payments with optional filters."""
    query = (
        select(TuitionPayment, Student.name.label("student_name"))
        .join(Student, TuitionPayment.student_id == Student.id)
        .where(TuitionPayment.center_id == center_id)
        .order_by(TuitionPayment.created_at.desc())
    )
    if student_id:
        query = query.where(TuitionPayment.student_id == student_id)
    if from_date:
        query = query.where(TuitionPayment.payment_date >= from_date)
    if to_date:
        query = query.where(TuitionPayment.payment_date <= to_date)

    result = await db.execute(query)
    rows = result.all()

    return [
        {
            "id": str(p.id),
            "student_id": str(p.student_id),
            "student_name": name,
            "amount": p.amount,
            "payment_date": p.payment_date.isoformat(),
            "payment_method": p.payment_method,
            "notes": p.notes,
            "created_at": p.created_at.isoformat(),
        }
        for p, name in rows
    ]


async def get_student_balances(
    db: AsyncSession,
    center_id: UUID,
    balance_filter: str = "all",
) -> list[StudentBalanceResponse]:
    """Get tuition balances for all students in a center."""
    # Subquery for total paid per student
    paid_sub = (
        select(
            TuitionLedgerEntry.student_id,
            func.coalesce(
                func.sum(case((TuitionLedgerEntry.entry_type == "payment", TuitionLedgerEntry.amount), else_=0)),
                0,
            ).label("total_paid"),
            func.coalesce(
                func.sum(case((TuitionLedgerEntry.entry_type == "class_fee", TuitionLedgerEntry.amount), else_=0)),
                0,
            ).label("total_fees"),
        )
        .where(TuitionLedgerEntry.center_id == center_id)
        .group_by(TuitionLedgerEntry.student_id)
        .subquery()
    )

    query = (
        select(
            Student.id,
            Student.name,
            Student.balance,
            func.coalesce(paid_sub.c.total_paid, 0).label("total_paid"),
            func.coalesce(paid_sub.c.total_fees, 0).label("total_fees"),
        )
        .outerjoin(paid_sub, Student.id == paid_sub.c.student_id)
        .where(Student.center_id == center_id)
        .order_by(Student.name)
    )

    if balance_filter == "positive":
        query = query.where(Student.balance > 0)
    elif balance_filter == "zero":
        query = query.where(Student.balance == 0)
    elif balance_filter == "negative":
        query = query.where(Student.balance < 0)

    result = await db.execute(query)
    rows = result.all()

    return [
        StudentBalanceResponse(
            student_id=row.id,
            student_name=row.name,
            total_paid=row.total_paid,
            total_fees=row.total_fees,
            balance=row.balance,
        )
        for row in rows
    ]


async def get_student_ledger(
    db: AsyncSession,
    student_id: UUID,
    center_id: UUID,
    from_date: date | None = None,
    to_date: date | None = None,
) -> StudentLedgerResponse:
    """Get chronological ledger for a student."""
    # Get student info
    student_result = await db.execute(
        select(Student).where(Student.id == student_id, Student.center_id == center_id)
    )
    student = student_result.scalar_one_or_none()
    if not student:
        raise ValueError(f"Student {student_id} not found in this center")

    # Build ledger query
    query = (
        select(TuitionLedgerEntry)
        .where(
            TuitionLedgerEntry.student_id == student_id,
            TuitionLedgerEntry.center_id == center_id,
        )
        .order_by(TuitionLedgerEntry.created_at.asc())
    )
    if from_date:
        query = query.where(TuitionLedgerEntry.entry_date >= from_date)
    if to_date:
        query = query.where(TuitionLedgerEntry.entry_date <= to_date)
    result = await db.execute(query)
    entries = result.scalars().all()

    entry_responses = []
    for entry in entries:
        class_display_id = None
        attendance_status = None
        charge_fee = None
        if entry.entry_type == "class_fee":
            # Prefer the actual class name via the lesson → class_ relationship
            # (both are eager-loaded via selectin, so no extra DB queries)
            if entry.lesson and entry.lesson.class_:
                class_display_id = entry.lesson.class_.name
            else:
                # Fallback: description was written as class name at attendance-mark time
                class_display_id = entry.description or None

            if entry.attendance:
                attendance_status = entry.attendance.status
                charge_fee = entry.attendance.charge_fee

        entry_responses.append(
            LedgerEntryResponse(
                id=entry.id,
                entry_type=entry.entry_type,
                amount=entry.amount,
                balance_after=entry.balance_after,
                description=entry.description,
                entry_date=entry.entry_date,
                class_display_id=class_display_id,
                attendance_status=attendance_status,
                charge_fee=charge_fee,
                created_at=entry.created_at,
            )
        )

    # Calculate all-time totals
    totals_query = select(
        func.coalesce(
            func.sum(case((TuitionLedgerEntry.entry_type == "payment", TuitionLedgerEntry.amount), else_=0)), 0
        ),
        func.coalesce(
            func.sum(case((TuitionLedgerEntry.entry_type == "class_fee", TuitionLedgerEntry.amount), else_=0)), 0
        ),
    ).where(
        TuitionLedgerEntry.student_id == student_id,
        TuitionLedgerEntry.center_id == center_id,
    )
    totals_result = await db.execute(totals_query)
    total_paid, total_fees = totals_result.one()

    return StudentLedgerResponse(
        student_id=student.id,
        student_name=student.name,
        current_balance=student.balance,
        total_paid=total_paid,
        total_fees=total_fees,
        entries=entry_responses,
    )
