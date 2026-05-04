"""Tuition API routes — payments, balances, ledger."""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.core.deps import CurrentUser, DbSession, get_center_id, require_role
from app.schemas.tuition import TuitionPaymentCreate
from app.services import tuition_service

router = APIRouter(prefix="/tuition", tags=["Tuition"])


@router.post("/payments", status_code=status.HTTP_201_CREATED)
@require_role("admin")
async def create_payment(
    data: TuitionPaymentCreate,
    db: DbSession,
    current_user: CurrentUser,
):
    """Record a tuition payment for a student. Admin only."""
    center_id = get_center_id(current_user)
    try:
        result = await tuition_service.record_payment(db, data, current_user.id, center_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/payments")
@require_role("admin")
async def list_payments(
    db: DbSession,
    current_user: CurrentUser,
    student_id: UUID | None = Query(None),
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
):
    """List tuition payments. Admin only."""
    center_id = get_center_id(current_user)
    return await tuition_service.list_payments(db, center_id, student_id, from_date, to_date)


@router.get("/balances")
@require_role("admin")
async def list_balances(
    db: DbSession,
    current_user: CurrentUser,
    balance_filter: str = Query("all"),
):
    """List all student tuition balances. Admin only."""
    center_id = get_center_id(current_user)
    return await tuition_service.get_student_balances(db, center_id, balance_filter)


@router.get("/ledger/{student_id}")
async def get_student_ledger(
    student_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
    from_date: date | None = Query(None),
    to_date: date | None = Query(None),
):
    """Get chronological ledger for a student.

    Admin: full detail.
    Parent: own child only, amounts hidden.
    """
    center_id = get_center_id(current_user)

    try:
        ledger = await tuition_service.get_student_ledger(db, student_id, center_id, from_date, to_date)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    # For parent role: hide financial amounts
    if current_user.role == "parent":
        # Verify student belongs to parent (via contact relationship)
        from sqlalchemy import select

        from app.models.student import Student

        result = await db.execute(select(Student).where(Student.id == student_id, Student.center_id == center_id))
        student = result.scalar_one_or_none()
        if not student:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

        # Check if parent has access (via contact JSON field)
        parent_user_id = str(current_user.id)
        contact = student.contact or {}
        if contact.get("user_id") != parent_user_id and contact.get("parent_user_id") != parent_user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        # Strip amounts for parent view
        for entry in ledger.entries:
            entry.amount = 0  # hide actual amounts

    elif current_user.role not in ("admin",):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return ledger


@router.get("/my-child/{student_id}/balance")
async def get_child_balance(
    student_id: UUID,
    db: DbSession,
    current_user: CurrentUser,
):
    """Get simplified tuition status for a parent's child."""
    if current_user.role != "parent":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Parent access only")

    center_id = get_center_id(current_user)

    from sqlalchemy import func, select

    from app.models.student import Student
    from app.models.tuition_ledger_entry import TuitionLedgerEntry

    # Verify student belongs to parent
    result = await db.execute(select(Student).where(Student.id == student_id, Student.center_id == center_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

    contact = student.contact or {}
    parent_user_id = str(current_user.id)
    if contact.get("user_id") != parent_user_id and contact.get("parent_user_id") != parent_user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # Count class_fee entries (classes attended)
    count_result = await db.execute(
        select(func.count()).where(
            TuitionLedgerEntry.student_id == student_id,
            TuitionLedgerEntry.entry_type == "class_fee",
            TuitionLedgerEntry.center_id == center_id,
        )
    )
    classes_attended = count_result.scalar() or 0

    # Sum payments
    paid_result = await db.execute(
        select(func.coalesce(func.sum(TuitionLedgerEntry.amount), 0)).where(
            TuitionLedgerEntry.student_id == student_id,
            TuitionLedgerEntry.entry_type == "payment",
            TuitionLedgerEntry.center_id == center_id,
        )
    )
    total_paid = paid_result.scalar() or 0

    return {
        "student_name": student.name,
        "total_paid": total_paid,
        "classes_attended": classes_attended,
        "current_balance": student.balance,
    }
