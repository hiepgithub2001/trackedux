"""LessonKind SQLAlchemy ORM model — append-only vocabulary."""

from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin, UUIDMixin


class LessonKind(Base, UUIDMixin, TimestampMixin):
    """A passive, append-only vocabulary entry for classifying course packages."""

    __tablename__ = "lesson_kinds"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    name_normalized: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True
    )
