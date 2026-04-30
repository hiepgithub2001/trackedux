"""ClassEnrollment SQLAlchemy ORM model (join table)."""

import uuid
from datetime import UTC, date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin


class ClassEnrollment(Base, UUIDMixin):
    """Links students to classes (new Class entity).

    class_session_id is kept temporarily for backward compatibility during migration.
    class_id is the new FK pointing to the classes table.
    """

    __tablename__ = "class_enrollments"
    __table_args__ = (UniqueConstraint("class_session_id", "student_id", name="uq_enrollment_class_student"),)

    # Legacy FK — kept during migration, will be dropped in migration 022
    class_session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("class_sessions.id"), nullable=False
    )
    # New FK → classes table (populated by migration 021)
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
    class_session = relationship("ClassSession", back_populates="enrollments")
    class_ = relationship("Class", back_populates="enrollments")
    student = relationship("Student", lazy="selectin")
