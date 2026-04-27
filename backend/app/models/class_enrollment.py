"""ClassEnrollment SQLAlchemy ORM model (join table)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin


class ClassEnrollment(Base, UUIDMixin):
    """Links students to class sessions."""

    __tablename__ = "class_enrollments"
    __table_args__ = (
        UniqueConstraint("class_session_id", "student_id", name="uq_enrollment_class_student"),
    )

    class_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("class_sessions.id"), nullable=False
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=False, index=True
    )
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    # Relationships
    class_session = relationship("ClassSession", back_populates="enrollments")
    student = relationship("Student", lazy="selectin")
