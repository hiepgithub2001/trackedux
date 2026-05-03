"""Pydantic schemas for Class CRUD operations."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ClassCreate(BaseModel):
    name: str = Field(..., max_length=200)
    teacher_id: uuid.UUID
    tuition_fee_per_lesson: int | None = Field(None, ge=0)
    lesson_kind_id: uuid.UUID | None = None
    student_ids: list[uuid.UUID] = Field(default_factory=list)


class ClassUpdate(BaseModel):
    name: str | None = Field(None, max_length=200)
    teacher_id: uuid.UUID | None = None
    tuition_fee_per_lesson: int | None = None
    lesson_kind_id: uuid.UUID | None = None
    is_active: bool | None = None


class EnrolledStudent(BaseModel):
    id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}


class ClassResponse(BaseModel):
    id: uuid.UUID
    name: str
    teacher_id: uuid.UUID
    teacher_name: str | None = None
    tuition_fee_per_lesson: int | None = None  # None for non-admin
    lesson_kind_id: uuid.UUID | None = None
    lesson_kind_name: str | None = None
    is_active: bool
    enrolled_count: int = 0
    enrolled_students: list[EnrolledStudent] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ClassEnrollRequest(BaseModel):
    student_id: uuid.UUID
    enrolled_since: str | None = None  # YYYY-MM-DD


class ClassUnenrollRequest(BaseModel):
    unenrolled_at: str | None = None  # YYYY-MM-DD
