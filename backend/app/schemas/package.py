"""Package Pydantic schemas."""
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PackageCreate(BaseModel):
    student_id: UUID
    total_sessions: int = Field(..., ge=1)
    package_type: str  # 12, 24, 36, custom
    price: int = Field(..., ge=0)


class PackageResponse(BaseModel):
    id: UUID
    student_id: UUID
    total_sessions: int
    remaining_sessions: int
    package_type: str
    price: int
    payment_status: str
    is_active: bool
    reminder_status: str
    started_at: date
    expired_at: date | None = None
    student_name: str | None = None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class PaymentRecordCreate(BaseModel):
    amount: int = Field(..., ge=0)
    payment_date: date
    payment_method: str | None = None
    notes: str | None = None


class PaymentRecordResponse(BaseModel):
    id: UUID
    package_id: UUID
    amount: int
    payment_date: date
    payment_method: str | None = None
    notes: str | None = None
    created_at: datetime
    model_config = {"from_attributes": True}
