"""Package Pydantic schemas — restructured for flexible course packages."""
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PackageCreate(BaseModel):
    student_id: UUID
    class_session_id: UUID
    number_of_lessons: int = Field(..., ge=1, le=500)
    tuition_fee: int = Field(..., ge=1, le=1_000_000_000)


class PackageUpdate(BaseModel):
    class_session_id: UUID | None = None
    number_of_lessons: int | None = Field(None, ge=1, le=500)
    tuition_fee: int | None = Field(None, ge=1, le=1_000_000_000)


class PackageResponse(BaseModel):
    id: UUID
    student_id: UUID
    student_name: str | None = None
    class_session_id: UUID
    class_display_id: str | None = None
    number_of_lessons: int
    remaining_sessions: int
    price: int | None = None  # None when hidden from non-admin
    payment_status: str
    is_active: bool
    reminder_status: str
    started_at: date
    expired_at: date | None = None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}


class PaymentRecordCreate(BaseModel):
    payment_date: date | None = None
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
