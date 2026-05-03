"""Lesson SQLAlchemy ORM model — schedule definition (one-off or recurring via RRULE)."""

import uuid
from datetime import date, time

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class Lesson(Base, UUIDMixin, TimestampMixin):
    """A schedulable definition attached to a Class.

    Either a one-off (specific_date set) or a recurring appointment (rrule set).
    Occurrences are computed at read time; persisted only when mutated by admin.
    """

    __tablename__ = "lessons"

    class_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id"), nullable=True, index=True
    )
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teachers.id"), nullable=False, index=True
    )
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    # Denormalized from RRULE BYDAY — kept for conflict-detection queries
    day_of_week: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    specific_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    # RFC 5545 RRULE string, e.g. "FREQ=WEEKLY;BYDAY=MO;COUNT=10"
    rrule: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", index=True)
    center_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("centers.id"), nullable=False, index=True
    )

    # Relationships
    class_ = relationship("Class", back_populates="lessons", lazy="selectin")
    teacher = relationship("Teacher", lazy="selectin")
    occurrences = relationship("LessonOccurrence", back_populates="lesson", lazy="selectin")
