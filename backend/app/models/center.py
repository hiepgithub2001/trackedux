"""Center SQLAlchemy ORM model."""

import uuid

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class Center(Base, UUIDMixin, TimestampMixin):
    """An edu-center tenant managed by the system admin."""

    __tablename__ = "centers"

    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)
    code: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    registered_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    # Relationships
    registered_by = relationship("User", foreign_keys=[registered_by_id], lazy="selectin")
