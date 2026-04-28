"""Create attendance_records table.

Revision ID: 007
Revises: 006
Create Date: 2026-04-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = "008"
down_revision: str | None = "007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "attendance_records",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("class_session_id", UUID(as_uuid=True), sa.ForeignKey("class_sessions.id"), nullable=False),
        sa.Column("student_id", UUID(as_uuid=True), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("package_id", UUID(as_uuid=True), sa.ForeignKey("packages.id"), nullable=True),
        sa.Column("session_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("makeup_scheduled", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("makeup_session_id", UUID(as_uuid=True), sa.ForeignKey("class_sessions.id"), nullable=True),
        sa.Column("marked_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "class_session_id", "student_id", "session_date", name="uq_attendance_session_student_date"
        ),
    )
    op.create_index("ix_attendance_student_id", "attendance_records", ["student_id"])
    op.create_index("ix_attendance_session_date", "attendance_records", ["session_date"])


def downgrade() -> None:
    op.drop_table("attendance_records")
