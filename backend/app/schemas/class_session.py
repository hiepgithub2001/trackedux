"""ClassSession Pydantic schemas."""

from datetime import date, datetime, time, timedelta
from uuid import UUID

from pydantic import BaseModel, Field


def _derive_end_time(start_time_str: str, duration_minutes: int) -> str:
    """Compute end time string from a HH:MM start and a duration in minutes."""
    st = time.fromisoformat(start_time_str)
    anchor = datetime.combine(date.today(), st)
    return (anchor + timedelta(minutes=duration_minutes)).time().strftime("%H:%M")


class ClassSessionCreate(BaseModel):
    """Schema for creating a class session."""

    teacher_id: UUID
    name: str = Field(..., min_length=1, max_length=200)
    day_of_week: int = Field(..., ge=0, le=6)
    start_time: str  # HH:MM format
    duration_minutes: int = Field(..., gt=0)
    tuition_fee_per_lesson: int | None = Field(None, ge=1, le=100_000_000)
    lesson_kind_name: str | None = Field(None, min_length=1, max_length=100)
    is_recurring: bool = True
    student_ids: list[UUID] = []


class ClassSessionUpdate(BaseModel):
    """Schema for updating a class session."""

    name: str | None = Field(None, min_length=1, max_length=200)
    day_of_week: int | None = Field(None, ge=0, le=6)
    start_time: str | None = None
    duration_minutes: int | None = Field(None, gt=0)
    tuition_fee_per_lesson: int | None = Field(None, ge=1, le=100_000_000)
    lesson_kind_name: str | None = Field(None, min_length=1, max_length=100)
    is_active: bool | None = None


class EnrollRequest(BaseModel):
    """Schema for enrolling a student in a class."""

    student_id: UUID


class ClassSessionResponse(BaseModel):
    """Schema for class session response."""

    id: UUID
    teacher_id: UUID
    name: str
    day_of_week: int
    start_time: str
    duration_minutes: int
    end_time: str  # derived: start_time + duration_minutes
    is_recurring: bool
    is_makeup: bool
    is_active: bool
    teacher_name: str | None = None
    display_id: str | None = None
    enrolled_count: int = 0
    tuition_fee_per_lesson: int | None = None
    lesson_kind_id: UUID | None = None
    lesson_kind_name: str | None = None
    enrolled_students: list[dict] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WeeklyScheduleResponse(BaseModel):
    """Schema for weekly schedule data."""

    week_start: date
    week_end: date
    sessions: list[dict]
