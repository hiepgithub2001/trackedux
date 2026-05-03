"""Tuition Pydantic schemas."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class TuitionPaymentCreate(BaseModel):
    student_id: UUID
    amount: int = Field(..., gt=0, le=1_000_000_000)
    payment_date: date | None = None  # defaults to today in service
    payment_method: str | None = None  # cash, bank_transfer, other
    notes: str | None = None


class TuitionPaymentResponse(BaseModel):
    id: UUID
    student_id: UUID
    student_name: str
    amount: int
    payment_date: date
    payment_method: str | None = None
    notes: str | None = None
    recorded_by: UUID
    balance_after: int
    created_at: datetime

    model_config = {"from_attributes": True}


class StudentBalanceResponse(BaseModel):
    student_id: UUID
    student_name: str
    enrollment_status: str
    total_paid: int
    total_fees: int
    balance: int


class LedgerEntryResponse(BaseModel):
    id: UUID
    entry_type: str  # "payment" or "class_fee"
    amount: int
    balance_after: int
    description: str
    entry_date: date
    class_display_id: str | None = None
    attendance_status: str | None = None  # present, absent, absent_with_notice
    charge_fee: bool | None = None  # whether this session was charged
    created_at: datetime

    model_config = {"from_attributes": True}


class StudentLedgerResponse(BaseModel):
    student_id: UUID
    student_name: str
    current_balance: int
    total_paid: int
    total_fees: int
    entries: list[LedgerEntryResponse]
