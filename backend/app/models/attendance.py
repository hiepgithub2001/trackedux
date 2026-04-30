"""AttendanceRecord SQLAlchemy ORM model."""

import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class AttendanceRecord(Base, UUIDMixin, TimestampMixin):
    """Per-student, per-session attendance log."""

    __tablename__ = "attendance_records"

    # FK → lesson_occurrences (new model); lesson_occurrence_id is the canonical ref
    lesson_occurrence_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lesson_occurrences.id"), nullable=True, index=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=False, index=True
    )
    session_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False)  # present, absent, absent_with_notice
    # whether to deduct class fee
    charge_fee: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    marked_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    center_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("centers.id"), nullable=False, index=True
    )

    # Relationships
    student = relationship("Student", lazy="selectin")
    lesson_occurrence = relationship("LessonOccurrence", lazy="selectin")
