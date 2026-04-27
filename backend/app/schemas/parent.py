"""Parent Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ParentCreate(BaseModel):
    """Schema for creating a parent."""

    full_name: str = Field(..., min_length=1, max_length=200)
    phone: str = Field(..., min_length=1, max_length=20)
    phone_secondary: str | None = None
    address: str | None = None
    notes: str | None = None


class ParentUpdate(BaseModel):
    """Schema for updating parent fields."""

    full_name: str | None = None
    phone: str | None = None
    phone_secondary: str | None = None
    address: str | None = None
    notes: str | None = None


class ParentResponse(BaseModel):
    """Schema for parent response data."""

    id: UUID
    full_name: str
    phone: str
    phone_secondary: str | None = None
    address: str | None = None
    zalo_id: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ParentBrief(BaseModel):
    """Minimal parent info for list views."""

    id: UUID
    full_name: str
    phone: str

    model_config = {"from_attributes": True}
