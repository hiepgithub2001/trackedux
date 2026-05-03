"""ClassEnrollment SQLAlchemy ORM model (join table)."""

import uuid
from datetime import UTC, date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin


class ClassEnrollment(Base, UUIDMixin):
    """Links students to the new Class entity.

    class_id is the canonical FK. class_session_id has been dropped in migration 022.
    enrolled_since / unenrolled_at support mid-series roster changes.
    """

    __tablename__ = "class_enrollments"

    # FK → classes table
    class_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("classes.id"), nullable=True, index=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=False, index=True
    )
    enrolled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        server_default=func.now(),
        nullable=False,
    )
    # Date from which enrollment is effective (for mid-series enrollment)
    enrolled_since: Mapped[date | None] = mapped_column(Date, nullable=True)
    # Date from which student is removed (for mid-series removal)
    unenrolled_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    center_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("centers.id"), nullable=False, index=True
    )

    # Relationships
    class_ = relationship("Class", back_populates="enrollments")
    student = relationship("Student", lazy="selectin")
