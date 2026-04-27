"""User Pydantic schemas for request/response validation."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    username: str = Field(..., min_length=3, max_length=100)
    email: str | None = None
    password: str = Field(..., min_length=6)
    role: str = Field(..., pattern="^(admin|staff|parent)$")
    full_name: str = Field(..., min_length=1, max_length=200)
    language: str = Field(default="vi", pattern="^(vi|en)$")


class UserUpdate(BaseModel):
    """Schema for updating user fields."""

    email: str | None = None
    full_name: str | None = None
    language: str | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    """Schema for user response data."""

    id: UUID
    username: str
    email: str | None = None
    role: str
    full_name: str
    language: str
    is_active: bool
    center_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    """Schema for login request."""

    username: str
    password: str


class TokenResponse(BaseModel):
    """Schema for authentication token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshRequest(BaseModel):
    """Schema for token refresh request."""

    refresh_token: str
