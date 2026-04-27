"""Create packages, payment_records, and renewal_reminders tables.

Revision ID: 008
Revises: 007
Create Date: 2026-04-27
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        "packages",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("student_id", UUID(as_uuid=True), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("total_sessions", sa.Integer(), nullable=False),
        sa.Column("remaining_sessions", sa.Integer(), nullable=False),
        sa.Column("package_type", sa.String(20), nullable=False),
        sa.Column("price", sa.BigInteger(), nullable=False),
        sa.Column("payment_status", sa.String(20), server_default="unpaid", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("reminder_status", sa.String(20), server_default="none", nullable=False),
        sa.Column("started_at", sa.Date(), nullable=False),
        sa.Column("expired_at", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_packages_student_id", "packages", ["student_id"])
    op.create_index("ix_packages_payment_status", "packages", ["payment_status"])

    op.create_table(
        "payment_records",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("package_id", UUID(as_uuid=True), sa.ForeignKey("packages.id"), nullable=False),
        sa.Column("amount", sa.BigInteger(), nullable=False),
        sa.Column("payment_date", sa.Date(), nullable=False),
        sa.Column("payment_method", sa.String(50), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("recorded_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payment_records_package_id", "payment_records", ["package_id"])

    op.create_table(
        "renewal_reminders",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("package_id", UUID(as_uuid=True), sa.ForeignKey("packages.id"), nullable=False),
        sa.Column("reminder_number", sa.Integer(), nullable=False),
        sa.Column("triggered_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("notification_id", UUID(as_uuid=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("package_id", "reminder_number", name="uq_renewal_package_number"),
    )

def downgrade() -> None:
    op.drop_table("renewal_reminders")
    op.drop_table("payment_records")
    op.drop_table("packages")
