"""Class SQLAlchemy ORM model — cohort definition (name, teacher, roster, tuition)."""

import uuid

from sqlalchemy import BigInteger, Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class Class(Base, UUIDMixin, TimestampMixin):
    """A named class cohort with a teacher and enrolled students.

    Scheduling lives in Lesson; this entity holds only cohort definition.
    """

    __tablename__ = "classes"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teachers.id"), nullable=False, index=True
    )
    tuition_fee_per_lesson: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    lesson_kind_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lesson_kinds.id"), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", index=True)
    center_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("centers.id"), nullable=False, index=True
    )

    # Relationships
    teacher = relationship("Teacher", lazy="selectin")
    enrollments = relationship("ClassEnrollment", back_populates="class_", lazy="selectin")
    lessons = relationship("Lesson", back_populates="class_", lazy="selectin")
    lesson_kind = relationship("LessonKind", lazy="selectin")
