"""ClassSession Pydantic schemas."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ClassSessionCreate(BaseModel):
    """Schema for creating a class session."""

    teacher_id: UUID
    class_type: str = Field(..., pattern="^(individual|pair|group)$")
    title: str | None = None
    day_of_week: int = Field(..., ge=0, le=6)
    start_time: str  # HH:MM format
    end_time: str
    is_recurring: bool = True
    student_ids: list[UUID] = []


class ClassSessionUpdate(BaseModel):
    """Schema for updating a class session."""

    title: str | None = None
    day_of_week: int | None = None
    start_time: str | None = None
    end_time: str | None = None
    is_active: bool | None = None


class EnrollRequest(BaseModel):
    """Schema for enrolling a student in a class."""

    student_id: UUID


class ClassSessionResponse(BaseModel):
    """Schema for class session response."""

    id: UUID
    teacher_id: UUID
    class_type: str
    title: str | None = None
    day_of_week: int
    start_time: str
    end_time: str
    is_recurring: bool
    is_makeup: bool
    max_students: int
    is_active: bool
    teacher_name: str | None = None
    enrolled_students: list[dict] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WeeklyScheduleResponse(BaseModel):
    """Schema for weekly schedule data."""

    week_start: date
    week_end: date
    sessions: list[dict]
