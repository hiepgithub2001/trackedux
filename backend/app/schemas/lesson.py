"""Pydantic schemas for Lesson CRUD and occurrence overrides."""

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class LessonCreate(BaseModel):
    class_id: uuid.UUID | None = None
    teacher_id: uuid.UUID
    title: str | None = Field(None, max_length=200)
    start_time: str  # HH:MM
    duration_minutes: int = Field(..., gt=0)
    specific_date: date | None = None
    rrule: str | None = Field(None, max_length=500)

    @model_validator(mode="after")
    def validate_schedule(self) -> "LessonCreate":
        has_date = self.specific_date is not None
        has_rrule = self.rrule is not None
        if has_date == has_rrule:  # both True or both False
            raise ValueError("Exactly one of specific_date or rrule must be provided")
        return self


class LessonSeriesUpdate(BaseModel):
    scope: Literal["series"]
    start_time: str | None = None  # HH:MM
    duration_minutes: int | None = Field(None, gt=0)
    rrule: str | None = Field(None, max_length=500)
    title: str | None = Field(None, max_length=200)
    teacher_id: uuid.UUID | None = None
    specific_date: date | None = None


class LessonResponse(BaseModel):
    id: uuid.UUID
    class_id: uuid.UUID | None = None
    class_name: str | None = None
    teacher_id: uuid.UUID
    teacher_name: str | None = None
    title: str | None = None
    start_time: str  # HH:MM
    duration_minutes: int
    day_of_week: int | None = None
    specific_date: date | None = None
    rrule: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OccurrenceOverrideRequest(BaseModel):
    action: Literal["cancel", "reschedule", "revert"]
    override_date: date | None = None
    override_start_time: str | None = None  # HH:MM

    @model_validator(mode="after")
    def validate_reschedule(self) -> "OccurrenceOverrideRequest":
        if self.action == "reschedule" and self.override_date is None:
            raise ValueError("override_date is required for reschedule action")
        return self


class OccurrenceResponse(BaseModel):
    id: uuid.UUID
    lesson_id: uuid.UUID
    original_date: date
    status: str
    override_date: date | None = None
    override_start_time: str | None = None
    center_id: uuid.UUID

    model_config = {"from_attributes": True}
