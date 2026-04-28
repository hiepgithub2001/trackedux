"""Teacher SQLAlchemy ORM model."""

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class Teacher(Base, UUIDMixin, TimestampMixin):
    """Instructor who teaches classes."""

    __tablename__ = "teachers"

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), unique=True, nullable=True
    )
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True, default="#1677ff")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true", index=True)
    center_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("centers.id"), nullable=False, index=True
    )

    # Relationships
    availability = relationship(
        "TeacherAvailability", back_populates="teacher", lazy="selectin", cascade="all, delete-orphan"
    )
    classes = relationship("ClassSession", back_populates="teacher", lazy="selectin")
