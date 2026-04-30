"""LessonOccurrence SQLAlchemy ORM model — lazily persisted per-occurrence override."""

import uuid
from datetime import date, time

from sqlalchemy import Date, ForeignKey, String, Time, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class LessonOccurrence(Base, UUIDMixin, TimestampMixin):
    """A persisted override for a single occurrence of a Lesson.

    Created lazily only when an admin takes a mutating action:
    marking attendance, canceling, or rescheduling an occurrence.
    Keyed on (lesson_id, original_date) — overrides always win over the series rule.
    """

    __tablename__ = "lesson_occurrences"
    __table_args__ = (
        UniqueConstraint("lesson_id", "original_date", name="uq_lesson_occurrence_lesson_date"),
    )

    lesson_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lessons.id"), nullable=False, index=True
    )
    # The date this occurrence falls on per the recurrence rule — immutable after creation
    original_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active", server_default="active")
    # Set when occurrence is rescheduled to a different date
    override_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    # Set when occurrence time is overridden
    override_start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    center_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("centers.id"), nullable=False, index=True
    )

    # Relationships
    lesson = relationship("Lesson", back_populates="occurrences", lazy="selectin")
