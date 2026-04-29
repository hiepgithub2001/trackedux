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

    class_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("class_sessions.id"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=False, index=True
    )
    session_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False)  # present, absent, absent_with_notice
    # whether to deduct class fee
    charge_fee: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    makeup_scheduled: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    makeup_session_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("class_sessions.id"), nullable=True
    )
    marked_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    center_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("centers.id"), nullable=False, index=True
    )

    # Relationships
    student = relationship("Student", lazy="selectin")
    class_session = relationship("ClassSession", foreign_keys=[class_session_id], lazy="selectin")
