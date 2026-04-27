"""ClassSession SQLAlchemy ORM model."""

import uuid
from datetime import date, time

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class ClassSession(Base, UUIDMixin, TimestampMixin):
    """A recurring or one-off class session."""

    __tablename__ = "class_sessions"

    teacher_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("teachers.id"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # 0=Monday
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    is_makeup: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    makeup_for_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("class_sessions.id"), nullable=True
    )
    specific_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", index=True)

    # Relationships
    teacher = relationship("Teacher", back_populates="classes", lazy="selectin")
    enrollments = relationship("ClassEnrollment", back_populates="class_session", lazy="selectin")

    @property
    def end_time(self) -> time:
        """Derived end time = start_time + duration_minutes (wraps within a single day)."""
        from datetime import datetime, timedelta

        anchor = datetime.combine(date.today(), self.start_time)
        return (anchor + timedelta(minutes=self.duration_minutes)).time()
