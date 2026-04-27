"""TeacherAvailability SQLAlchemy ORM model."""

import uuid
from datetime import time

from sqlalchemy import ForeignKey, Integer, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin


class TeacherAvailability(Base, UUIDMixin):
    """Weekly availability slot for a teacher."""

    __tablename__ = "teacher_availability"

    teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teachers.id"), nullable=False, index=True
    )
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)

    # Relationships
    teacher = relationship("Teacher", back_populates="availability")
