"""021_class_lesson_separation

Separate ClassSession into Class (cohort) + Lesson (schedule).

Creates:
  - classes table
  - lessons table
  - lesson_occurrences table

Migrates existing class_sessions data into the new structure.
Adds new FKs to class_enrollments, attendance_records, tuition_ledger_entries.
Old class_sessions table is KEPT (dropped in migration 022 after smoke test).

Revision ID: 021
Revises: 020
Create Date: 2026-04-30
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers
revision: str = "021"
down_revision: str | None = "020"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Helpers
UUID_TYPE = postgresql.UUID(as_uuid=False)


def upgrade() -> None:
    # ──────────────────────────────────────────────
    # 1. Create classes table
    # ──────────────────────────────────────────────
    op.create_table(
        "classes",
        sa.Column("id", UUID_TYPE, primary_key=True, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("teacher_id", UUID_TYPE, sa.ForeignKey("teachers.id"), nullable=False),
        sa.Column("tuition_fee_per_lesson", sa.BigInteger, nullable=True),
        sa.Column("lesson_kind_id", UUID_TYPE, sa.ForeignKey("lesson_kinds.id"), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("center_id", UUID_TYPE, sa.ForeignKey("centers.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_classes_center_id", "classes", ["center_id"])
    op.create_index("ix_classes_teacher_id", "classes", ["teacher_id"])
    op.create_index("ix_classes_is_active", "classes", ["is_active"])

    # ──────────────────────────────────────────────
    # 2. Create lessons table
    # ──────────────────────────────────────────────
    op.create_table(
        "lessons",
        sa.Column("id", UUID_TYPE, primary_key=True, nullable=False),
        sa.Column("class_id", UUID_TYPE, sa.ForeignKey("classes.id"), nullable=True),
        sa.Column("teacher_id", UUID_TYPE, sa.ForeignKey("teachers.id"), nullable=False),
        sa.Column("title", sa.String(200), nullable=True),
        sa.Column("start_time", sa.Time, nullable=False),
        sa.Column("duration_minutes", sa.Integer, nullable=False),
        sa.Column("day_of_week", sa.Integer, nullable=True),
        sa.Column("specific_date", sa.Date, nullable=True),
        sa.Column("rrule", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("center_id", UUID_TYPE, sa.ForeignKey("centers.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_lessons_center_id", "lessons", ["center_id"])
    op.create_index("ix_lessons_class_id", "lessons", ["class_id"])
    op.create_index("ix_lessons_teacher_id", "lessons", ["teacher_id"])
    op.create_index("ix_lessons_day_of_week", "lessons", ["day_of_week"])
    op.create_index("ix_lessons_specific_date", "lessons", ["specific_date"])
    op.create_index("ix_lessons_is_active", "lessons", ["is_active"])

    # ──────────────────────────────────────────────
    # 3. Create lesson_occurrences table
    # ──────────────────────────────────────────────
    op.create_table(
        "lesson_occurrences",
        sa.Column("id", UUID_TYPE, primary_key=True, nullable=False),
        sa.Column("lesson_id", UUID_TYPE, sa.ForeignKey("lessons.id"), nullable=False),
        sa.Column("original_date", sa.Date, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("override_date", sa.Date, nullable=True),
        sa.Column("override_start_time", sa.Time, nullable=True),
        sa.Column("center_id", UUID_TYPE, sa.ForeignKey("centers.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("lesson_id", "original_date", name="uq_lesson_occurrence_lesson_date"),
    )
    op.create_index("ix_lesson_occurrences_lesson_id", "lesson_occurrences", ["lesson_id"])
    op.create_index("ix_lesson_occurrences_original_date", "lesson_occurrences", ["original_date"])
    op.create_index("ix_lesson_occurrences_center_id", "lesson_occurrences", ["center_id"])

    # ──────────────────────────────────────────────
    # 4. Add new columns to class_enrollments
    # ──────────────────────────────────────────────
    op.add_column("class_enrollments", sa.Column("class_id", UUID_TYPE, nullable=True))
    op.add_column("class_enrollments", sa.Column("enrolled_since", sa.Date, nullable=True))
    op.add_column("class_enrollments", sa.Column("unenrolled_at", sa.Date, nullable=True))
    op.create_foreign_key(
        "fk_class_enrollments_class_id",
        "class_enrollments", "classes",
        ["class_id"], ["id"],
    )
    op.create_index("ix_class_enrollments_class_id", "class_enrollments", ["class_id"])

    # ──────────────────────────────────────────────
    # 5. Add new columns to attendance_records and tuition_ledger_entries
    # ──────────────────────────────────────────────
    op.add_column(
        "attendance_records",
        sa.Column("lesson_occurrence_id", UUID_TYPE, nullable=True),
    )
    op.create_foreign_key(
        "fk_attendance_lesson_occurrence",
        "attendance_records", "lesson_occurrences",
        ["lesson_occurrence_id"], ["id"],
    )

    op.add_column(
        "tuition_ledger_entries",
        sa.Column("lesson_id", UUID_TYPE, nullable=True),
    )
    op.create_foreign_key(
        "fk_tuition_ledger_lesson",
        "tuition_ledger_entries", "lessons",
        ["lesson_id"], ["id"],
    )

    # ──────────────────────────────────────────────
    # 6. Data migration: class_sessions → classes + lessons
    # ──────────────────────────────────────────────
    conn = op.get_bind()

    # Fetch all class_sessions
    sessions = conn.execute(sa.text(
        """
        SELECT id, name, teacher_id, tuition_fee_per_lesson, lesson_kind_id,
               is_active, center_id, day_of_week, start_time, duration_minutes,
               is_recurring, recurring_pattern, specific_date, created_at, updated_at
        FROM class_sessions
        """
    )).fetchall()

    # Map: class_session_id → new class_id (str)
    session_to_class: dict[str, str] = {}
    # Map: class_session_id → new lesson_id (str)
    session_to_lesson: dict[str, str] = {}

    for row in sessions:
        new_class_id = str(uuid.uuid4())
        new_lesson_id = str(uuid.uuid4())
        session_to_class[str(row.id)] = new_class_id
        session_to_lesson[str(row.id)] = new_lesson_id

        # Build RRULE for recurring sessions
        rrule_val = None
        day_of_week_val = None
        specific_date_val = None

        if row.is_recurring and row.day_of_week is not None:
            byday_map = {0: "MO", 1: "TU", 2: "WE", 3: "TH", 4: "FR", 5: "SA", 6: "SU"}
            byday = byday_map.get(row.day_of_week, "MO")
            rrule_val = f"FREQ=WEEKLY;BYDAY={byday}"
            day_of_week_val = row.day_of_week
        elif row.specific_date is not None:
            specific_date_val = row.specific_date

        # Insert into classes
        conn.execute(sa.text(
            """
            INSERT INTO classes (id, name, teacher_id, tuition_fee_per_lesson,
                                 lesson_kind_id, is_active, center_id, created_at, updated_at)
            VALUES (:id, :name, :teacher_id, :fee, :lk_id, :is_active,
                    :center_id, :created_at, :updated_at)
            """
        ), {
            "id": new_class_id,
            "name": row.name,
            "teacher_id": str(row.teacher_id),
            "fee": row.tuition_fee_per_lesson,
            "lk_id": str(row.lesson_kind_id) if row.lesson_kind_id else None,
            "is_active": row.is_active,
            "center_id": str(row.center_id),
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        })

        # Insert into lessons
        conn.execute(sa.text(
            """
            INSERT INTO lessons (id, class_id, teacher_id, title, start_time,
                                 duration_minutes, day_of_week, specific_date,
                                 rrule, is_active, center_id, created_at, updated_at)
            VALUES (:id, :class_id, :teacher_id, NULL, :start_time,
                    :duration, :dow, :spec_date,
                    :rrule, :is_active, :center_id, :created_at, :updated_at)
            """
        ), {
            "id": new_lesson_id,
            "class_id": new_class_id,
            "teacher_id": str(row.teacher_id),
            "start_time": row.start_time,
            "duration": row.duration_minutes,
            "dow": day_of_week_val,
            "spec_date": specific_date_val,
            "rrule": rrule_val,
            "is_active": row.is_active,
            "center_id": str(row.center_id),
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        })

    # ──────────────────────────────────────────────
    # 7. Update class_enrollments.class_id from the mapping
    # ──────────────────────────────────────────────
    for session_id_str, class_id_str in session_to_class.items():
        conn.execute(sa.text(
            "UPDATE class_enrollments SET class_id = :class_id WHERE class_session_id = :session_id"
        ), {"class_id": class_id_str, "session_id": session_id_str})


def downgrade() -> None:
    # Remove FKs and columns added to existing tables
    op.drop_constraint("fk_tuition_ledger_lesson", "tuition_ledger_entries", type_="foreignkey")
    op.drop_column("tuition_ledger_entries", "lesson_id")

    op.drop_constraint("fk_attendance_lesson_occurrence", "attendance_records", type_="foreignkey")
    op.drop_column("attendance_records", "lesson_occurrence_id")

    op.drop_constraint("fk_class_enrollments_class_id", "class_enrollments", type_="foreignkey")
    op.drop_index("ix_class_enrollments_class_id", table_name="class_enrollments")
    op.drop_column("class_enrollments", "unenrolled_at")
    op.drop_column("class_enrollments", "enrolled_since")
    op.drop_column("class_enrollments", "class_id")

    # Drop new tables (data loss — migration is one-way without manual backup)
    op.drop_table("lesson_occurrences")
    op.drop_table("lessons")
    op.drop_table("classes")
