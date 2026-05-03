"""Attendance Pydantic schemas."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel


class AttendanceBatchItem(BaseModel):
    student_id: UUID
    status: str  # present, absent, absent_with_notice
    charge_fee: bool = True  # whether to deduct class fee for this student
    notes: str | None = None


class AttendanceBatchRequest(BaseModel):
    lesson_id: UUID
    session_date: date
    records: list[AttendanceBatchItem]


class AttendanceResponse(BaseModel):
    id: UUID
    class_session_id: UUID
    student_id: UUID
    session_date: date
    status: str
    notes: str | None = None
    created_at: datetime
    model_config = {"from_attributes": True}
