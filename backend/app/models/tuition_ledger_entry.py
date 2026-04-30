"""TuitionLedgerEntry SQLAlchemy ORM model."""

import uuid
from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, UUIDMixin


class TuitionLedgerEntry(Base, UUIDMixin):
    """An individual balance-affecting event in a student's tuition ledger.

    Type is either 'payment' (credit — balance increases) or 'class_fee' (debit — balance decreases).
    Amount is always stored as a positive integer; the sign is determined by entry_type.
    """

    __tablename__ = "tuition_ledger_entries"

    student_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("students.id"), nullable=False
    )
    entry_type: Mapped[str] = mapped_column(String(20), nullable=False)  # "payment" or "class_fee"
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)  # always positive
    balance_after: Mapped[int] = mapped_column(BigInteger, nullable=False)  # running balance snapshot

    # FK references — one of these will be set depending on entry_type
    payment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tuition_payments.id"), nullable=True
    )
    attendance_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("attendance_records.id"), nullable=True
    )
    # lesson_id: populated for lesson-based fee deductions (migration 021+)
    lesson_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("lessons.id"), nullable=True
    )

    entry_date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    center_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("centers.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    # Relationships
    student = relationship("Student", lazy="selectin")
    payment = relationship("TuitionPayment", lazy="selectin")
    attendance = relationship("AttendanceRecord", lazy="selectin")
    lesson = relationship("Lesson", lazy="selectin")

    __table_args__ = (
        # Composite index for chronological ledger queries
        Index("ix_ledger_student_created", "student_id", "created_at"),
        # Partial unique index: prevent duplicate deductions for the same attendance record
        Index(
            "ix_ledger_attendance_unique",
            "attendance_id",
            unique=True,
            postgresql_where=(attendance_id.isnot(None)),
        ),
        Index("ix_ledger_center", "center_id"),
        Index("ix_ledger_entry_date", "entry_date"),
    )
