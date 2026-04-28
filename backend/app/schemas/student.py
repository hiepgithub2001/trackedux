"""Student Pydantic schemas."""

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ContactInfo(BaseModel):
    """Schema for student contact information."""

    name: str | None = None
    relationship: str | None = None
    phone: str | None = None
    phone_secondary: str | None = None
    email: str | None = None
    address: str | None = None
    zalo_id: str | None = None
    notes: str | None = None


class StudentCreate(BaseModel):
    """Schema for creating a student."""

    name: str = Field(..., min_length=1, max_length=200)
    nickname: str | None = None
    date_of_birth: date | None = None
    age: int | None = None

    personality_notes: str | None = None
    learning_speed: str | None = None
    current_issues: str | None = None
    enrollment_status: str = Field(default="trial", pattern="^(trial|active|paused|withdrawn)$")
    contact: ContactInfo | None = None
    class_ids: list[UUID] | None = None


class StudentUpdate(BaseModel):
    """Schema for updating student fields."""

    name: str | None = None
    nickname: str | None = None
    date_of_birth: date | None = None
    age: int | None = None

    personality_notes: str | None = None
    learning_speed: str | None = None
    current_issues: str | None = None
    contact: ContactInfo | None = None
    class_ids: list[UUID] | None = None


class StudentStatusChange(BaseModel):
    """Schema for changing enrollment status."""

    status: str = Field(..., pattern="^(trial|active|paused|withdrawn)$")
    reason: str | None = None


class StudentResponse(BaseModel):
    """Schema for full student response."""

    id: UUID
    name: str
    nickname: str | None = None
    date_of_birth: date | None = None
    age: int | None = None

    personality_notes: str | None = None
    learning_speed: str | None = None
    current_issues: str | None = None
    enrollment_status: str
    enrolled_at: date
    contact: ContactInfo | None = None
    created_at: datetime
    updated_at: datetime
    class_ids: list[UUID] = []

    model_config = {"from_attributes": True}


class StudentListItem(BaseModel):
    """Schema for student list view."""

    id: UUID
    name: str
    nickname: str | None = None
    age: int | None = None

    enrollment_status: str
    enrolled_at: date
    contact_name: str | None = None

    model_config = {"from_attributes": True}


class PaginatedStudents(BaseModel):
    """Paginated list of students."""

    items: list[StudentListItem]
    total: int
    page: int
    page_size: int
