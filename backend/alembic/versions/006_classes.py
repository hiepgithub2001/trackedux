"""Create class_sessions and class_enrollments tables.

Revision ID: 006
Revises: 005
Create Date: 2026-04-27
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = "006"
down_revision: str | None = "005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "class_sessions",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("teacher_id", UUID(as_uuid=True), sa.ForeignKey("teachers.id"), nullable=False),
        sa.Column("class_type", sa.String(20), nullable=False),
        sa.Column("title", sa.String(200), nullable=True),
        sa.Column("day_of_week", sa.Integer(), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
        sa.Column("is_recurring", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("is_makeup", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("makeup_for_id", UUID(as_uuid=True), sa.ForeignKey("class_sessions.id"), nullable=True),
        sa.Column("specific_date", sa.Date(), nullable=True),
        sa.Column("max_students", sa.Integer(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_class_sessions_teacher_id", "class_sessions", ["teacher_id"])
    op.create_index("ix_class_sessions_day_of_week", "class_sessions", ["day_of_week"])
    op.create_index("ix_class_sessions_is_active", "class_sessions", ["is_active"])

    op.create_table(
        "class_enrollments",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("class_session_id", UUID(as_uuid=True), sa.ForeignKey("class_sessions.id"), nullable=False),
        sa.Column("student_id", UUID(as_uuid=True), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("enrolled_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("class_session_id", "student_id", name="uq_enrollment_class_student"),
    )
    op.create_index("ix_class_enrollments_student_id", "class_enrollments", ["student_id"])


def downgrade() -> None:
    op.drop_table("class_enrollments")
    op.drop_table("class_sessions")
