"""022_drop_class_sessions

Drop the legacy class_sessions table now that all data has been migrated
to the classes + lessons model (migration 021).

Also drops:
  - class_enrollments.class_session_id FK / column
  - attendance_records.class_session_id FK / column (legacy lookup replaced by lesson_occurrence_id)
  - attendance_records.makeup_session_id FK / column (never used in new model)

⚠️  DESTRUCTIVE — run only after smoke-testing migration 021 in production.
     The downgrade recreates the tables and columns but data is NOT restored.

Revision ID: 022
Revises: 021
Create Date: 2026-05-01
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "022"
down_revision: str | None = "021"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

UUID_TYPE = postgresql.UUID(as_uuid=False)


def upgrade() -> None:
    # ──────────────────────────────────────────────
    # 1. Drop legacy FK + unique constraint from class_enrollments
    # ──────────────────────────────────────────────
    op.drop_constraint(
        "uq_enrollment_class_student",
        "class_enrollments",
        type_="unique",
    )
    op.drop_constraint(
        "class_enrollments_class_session_id_fkey",
        "class_enrollments",
        type_="foreignkey",
    )
    op.drop_index("ix_class_enrollments_student_id", table_name="class_enrollments", if_exists=True)
    op.drop_column("class_enrollments", "class_session_id")

    # ──────────────────────────────────────────────
    # 2. Drop legacy FKs from attendance_records
    # ──────────────────────────────────────────────
    op.drop_constraint(
        "attendance_records_class_session_id_fkey",
        "attendance_records",
        type_="foreignkey",
    )
    op.drop_column("attendance_records", "class_session_id")

    op.drop_constraint(
        "attendance_records_makeup_session_id_fkey",
        "attendance_records",
        type_="foreignkey",
    )
    op.drop_column("attendance_records", "makeup_session_id")
    op.drop_column("attendance_records", "makeup_scheduled")

    # ──────────────────────────────────────────────
    # 3. Drop tuition_ledger_entries.class_session_id FK
    # ──────────────────────────────────────────────
    op.drop_constraint(
        "tuition_ledger_entries_class_session_id_fkey",
        "tuition_ledger_entries",
        type_="foreignkey",
    )
    op.drop_column("tuition_ledger_entries", "class_session_id")

    # ──────────────────────────────────────────────
    # 4. Drop class_sessions itself (all dependents gone)
    # ──────────────────────────────────────────────
    op.drop_index("ix_class_sessions_teacher_id", table_name="class_sessions", if_exists=True)
    op.drop_index("ix_class_sessions_day_of_week", table_name="class_sessions", if_exists=True)
    op.drop_index("ix_class_sessions_is_active", table_name="class_sessions", if_exists=True)
    op.drop_index("ix_class_sessions_lesson_kind_id", table_name="class_sessions", if_exists=True)
    op.drop_index("ix_class_sessions_center_id", table_name="class_sessions", if_exists=True)
    op.drop_table("class_sessions")


def downgrade() -> None:
    """Recreate class_sessions and dropped columns — DATA IS NOT RESTORED."""

    # Recreate class_sessions (schema only — data is lost)
    op.create_table(
        "class_sessions",
        sa.Column(
            "id",
            UUID_TYPE,
            server_default=sa.text("uuid_generate_v4()"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("name", sa.String(200), nullable=False, server_default=""),
        sa.Column("teacher_id", UUID_TYPE, sa.ForeignKey("teachers.id"), nullable=False),
        sa.Column("class_type", sa.String(20), nullable=False, server_default="group"),
        sa.Column("title", sa.String(200), nullable=True),
        sa.Column("day_of_week", sa.Integer(), nullable=True),
        sa.Column("start_time", sa.Time(), nullable=False, server_default="09:00"),
        sa.Column("end_time", sa.Time(), nullable=False, server_default="10:00"),
        sa.Column("is_recurring", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("is_makeup", sa.Boolean(), server_default="false", nullable=False),
        sa.Column(
            "makeup_for_id",
            UUID_TYPE,
            sa.ForeignKey("class_sessions.id"),
            nullable=True,
        ),
        sa.Column("specific_date", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("tuition_fee_per_lesson", sa.BigInteger(), nullable=True),
        sa.Column("lesson_kind_id", UUID_TYPE, sa.ForeignKey("lesson_kinds.id"), nullable=True),
        sa.Column("recurring_pattern", sa.String(20), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("center_id", UUID_TYPE, sa.ForeignKey("centers.id"), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_class_sessions_teacher_id", "class_sessions", ["teacher_id"])
    op.create_index("ix_class_sessions_day_of_week", "class_sessions", ["day_of_week"])
    op.create_index("ix_class_sessions_is_active", "class_sessions", ["is_active"])
    op.create_index("ix_class_sessions_lesson_kind_id", "class_sessions", ["lesson_kind_id"])
    op.create_index("ix_class_sessions_center_id", "class_sessions", ["center_id"])

    # Restore class_enrollments.class_session_id
    op.add_column(
        "class_enrollments",
        sa.Column("class_session_id", UUID_TYPE, nullable=True),
    )
    op.create_foreign_key(
        "class_enrollments_class_session_id_fkey",
        "class_enrollments",
        "class_sessions",
        ["class_session_id"],
        ["id"],
    )
    op.create_unique_constraint(
        "uq_enrollment_class_student",
        "class_enrollments",
        ["class_session_id", "student_id"],
    )
    op.create_index("ix_class_enrollments_student_id", "class_enrollments", ["student_id"], if_not_exists=True)

    # Restore attendance_records legacy columns
    op.add_column(
        "attendance_records",
        sa.Column("class_session_id", UUID_TYPE, nullable=True),
    )
    op.create_foreign_key(
        "attendance_records_class_session_id_fkey",
        "attendance_records",
        "class_sessions",
        ["class_session_id"],
        ["id"],
    )
    op.add_column(
        "attendance_records",
        sa.Column("makeup_session_id", UUID_TYPE, nullable=True),
    )
    op.create_foreign_key(
        "attendance_records_makeup_session_id_fkey",
        "attendance_records",
        "class_sessions",
        ["makeup_session_id"],
        ["id"],
    )
    op.add_column(
        "attendance_records",
        sa.Column("makeup_scheduled", sa.Boolean(), nullable=False, server_default="false"),
    )

    # Restore tuition_ledger_entries.class_session_id
    op.add_column(
        "tuition_ledger_entries",
        sa.Column("class_session_id", UUID_TYPE, nullable=True),
    )
    op.create_foreign_key(
        "tuition_ledger_entries_class_session_id_fkey",
        "tuition_ledger_entries",
        "class_sessions",
        ["class_session_id"],
        ["id"],
    )
