"""Package SQLAlchemy ORM model."""

import uuid
from datetime import date

from sqlalchemy import BigInteger, Boolean, Date, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin


class Package(Base, UUIDMixin, TimestampMixin):
    """A purchased bundle of sessions assigned to a student."""

    __tablename__ = "packages"

    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False, index=True)
    total_sessions: Mapped[int] = mapped_column(Integer, nullable=False)
    remaining_sessions: Mapped[int] = mapped_column(Integer, nullable=False)
    package_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 12, 24, 36, custom
    price: Mapped[int] = mapped_column(BigInteger, nullable=False)
    payment_status: Mapped[str] = mapped_column(String(20), nullable=False, default="unpaid", server_default="unpaid", index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    reminder_status: Mapped[str] = mapped_column(String(20), default="none", server_default="none")
    started_at: Mapped[date] = mapped_column(Date, nullable=False)
    expired_at: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Relationships
    student = relationship("Student", lazy="selectin")
    payments = relationship("PaymentRecord", back_populates="package", lazy="selectin")
