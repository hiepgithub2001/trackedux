"""Teacher Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class AvailabilitySlot(BaseModel):
    """A single availability time slot."""

    day_of_week: int = Field(..., ge=0, le=6)
    start_time: str  # HH:MM format
    end_time: str


class TeacherCreate(BaseModel):
    """Schema for creating a teacher."""

    full_name: str = Field(..., min_length=1, max_length=200)
    phone: str | None = None
    email: str | None = None
    notes: str | None = None


class TeacherUpdate(BaseModel):
    """Schema for updating teacher fields."""

    full_name: str | None = None
    phone: str | None = None
    email: str | None = None
    notes: str | None = None
    is_active: bool | None = None


class AvailabilityUpdate(BaseModel):
    """Schema for replacing availability slots."""

    slots: list[AvailabilitySlot]


class TeacherResponse(BaseModel):
    """Schema for teacher response."""

    id: UUID
    full_name: str
    phone: str | None = None
    email: str | None = None
    notes: str | None = None
    is_active: bool
    availability: list[AvailabilitySlot] = []
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TeacherBrief(BaseModel):
    """Minimal teacher info."""

    id: UUID
    full_name: str

    model_config = {"from_attributes": True}
