"""LessonKind SQLAlchemy ORM model — append-only vocabulary."""

import uuid

from sqlalchemy import ForeignKey, String, func  # noqa: F401
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class LessonKind(Base, UUIDMixin, TimestampMixin):
    """A passive, append-only vocabulary entry for classifying course lessons."""

    __tablename__ = "lesson_kinds"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    name_normalized: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    center_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("centers.id"), nullable=False, index=True
    )
