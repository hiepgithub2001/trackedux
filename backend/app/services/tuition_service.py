"""Tuition service — package management, payment recording."""
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.package import get_package_by_id
from app.models.payment_record import PaymentRecord
from app.schemas.package import PaymentRecordCreate


async def record_payment(db: AsyncSession, package_id: UUID, data: PaymentRecordCreate, recorded_by: UUID) -> PaymentRecord:
    pkg = await get_package_by_id(db, package_id)
    if pkg is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Package not found")

    from datetime import datetime, UTC
    payment_date = data.payment_date or datetime.now(UTC).date()
    
    payment = PaymentRecord(
        package_id=package_id, amount=pkg.price, payment_date=payment_date,
        payment_method=data.payment_method, notes=data.notes, recorded_by=recorded_by,
    )
    db.add(payment)

    # Update payment status
    pkg.payment_status = "paid"
    await db.commit()
    await db.refresh(payment)
    return payment
