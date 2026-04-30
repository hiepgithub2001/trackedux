"""Student SQLAlchemy ORM model."""

import uuid
from datetime import date

from sqlalchemy import BigInteger, Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class Student(Base, UUIDMixin, TimestampMixin):
    """A learner enrolled at the piano center."""

    __tablename__ = "students"

    contact: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    nickname: Mapped[str | None] = mapped_column(String(100), nullable=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)

    personality_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    learning_speed: Mapped[str | None] = mapped_column(String(50), nullable=True)
    current_issues: Mapped[str | None] = mapped_column(Text, nullable=True)
    enrollment_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="trial", server_default="trial", index=True
    )
    enrolled_at: Mapped[date] = mapped_column(Date, nullable=False)
    center_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("centers.id"), nullable=False, index=True
    )
    balance: Mapped[int] = mapped_column(
        BigInteger, nullable=False, default=0, server_default="0"
    )  # Cached tuition balance in VND. Updated atomically with each ledger entry.

    # Relationships
    status_history = relationship("StudentStatusHistory", back_populates="student", lazy="selectin")
    enrollments = relationship("ClassEnrollment", back_populates="student", lazy="selectin")

    @property
    def class_ids(self) -> list[uuid.UUID]:
        """Return the list of active class IDs for this student."""
        return [e.class_id for e in self.enrollments if getattr(e, "is_active", False) and e.class_id]
