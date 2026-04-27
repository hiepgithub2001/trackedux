"""Create parents, students, and student_status_history tables.

Revision ID: 004
Revises: 003
Create Date: 2026-04-27
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID


revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Parents table
    op.create_table(
        "parents",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("full_name", sa.String(200), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("phone_secondary", sa.String(20), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("zalo_id", sa.String(100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_parents_user_id", "parents", ["user_id"], unique=True)
    op.create_index("ix_parents_phone", "parents", ["phone"])

    # Students table
    op.create_table(
        "students",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("parent_id", UUID(as_uuid=True), sa.ForeignKey("parents.id"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("nickname", sa.String(100), nullable=True),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("age", sa.Integer(), nullable=True),
        sa.Column("skill_level", sa.String(50), nullable=False),
        sa.Column("personality_notes", sa.Text(), nullable=True),
        sa.Column("learning_speed", sa.String(50), nullable=True),
        sa.Column("current_issues", sa.Text(), nullable=True),
        sa.Column("enrollment_status", sa.String(20), server_default="trial", nullable=False),
        sa.Column("enrolled_at", sa.Date(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_students_parent_id", "students", ["parent_id"])
    op.create_index("ix_students_enrollment_status", "students", ["enrollment_status"])
    op.create_index("ix_students_skill_level", "students", ["skill_level"])
    op.create_index("ix_students_name", "students", ["name"])

    # Student status history table
    op.create_table(
        "student_status_history",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("student_id", UUID(as_uuid=True), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("from_status", sa.String(20), nullable=True),
        sa.Column("to_status", sa.String(20), nullable=False),
        sa.Column("changed_by", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("changed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_student_status_history_student_id", "student_status_history", ["student_id"])
    op.create_index("ix_student_status_history_changed_at", "student_status_history", ["changed_at"])


def downgrade() -> None:
    op.drop_table("student_status_history")
    op.drop_table("students")
    op.drop_table("parents")
