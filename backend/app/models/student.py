"""Student SQLAlchemy ORM model."""

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class Student(Base, UUIDMixin, TimestampMixin):
    """A learner enrolled at the piano center."""

    __tablename__ = "students"

    parent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("parents.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    nickname: Mapped[str | None] = mapped_column(String(100), nullable=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    skill_level: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    personality_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    learning_speed: Mapped[str | None] = mapped_column(String(50), nullable=True)
    current_issues: Mapped[str | None] = mapped_column(Text, nullable=True)
    enrollment_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="trial", server_default="trial", index=True
    )
    enrolled_at: Mapped[date] = mapped_column(Date, nullable=False)

    # Relationships
    parent = relationship("Parent", back_populates="students", lazy="selectin")
    status_history = relationship("StudentStatusHistory", back_populates="student", lazy="selectin")
