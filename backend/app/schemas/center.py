"""Center Pydantic schemas for request/response validation."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CenterCreate(BaseModel):
    """Schema for creating a new center."""

    name: str = Field(..., min_length=2, max_length=200)
    admin_full_name: str = Field(..., min_length=1, max_length=200)
    admin_username: str = Field(..., min_length=3, max_length=100)
    admin_email: str | None = None


class CenterResponse(BaseModel):
    """Schema for a center."""

    id: UUID
    name: str
    code: str
    is_active: bool
    registered_by_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CenterListItem(CenterResponse):
    """Schema for center list item including admin info."""
    
    admin_username: str | None = None
    admin_email: str | None = None


class AdminCredentials(BaseModel):
    """Schema for returning temporary admin credentials."""
    
    username: str
    temporary_password: str
    note: str = "Please copy and save this password immediately. It will not be shown again."


class CreateCenterResponse(BaseModel):
    """Schema for response after creating a center and its admin."""
    
    center: CenterResponse
    admin_credentials: AdminCredentials
