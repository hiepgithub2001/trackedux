"""Flexible course package: lesson_kinds, restructure packages, class fee, drop skill_level.

Revision ID: 012
Revises: 011
Create Date: 2026-04-27
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "012"
down_revision: Union[str, None] = "011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create lesson_kinds table
    op.create_table(
        "lesson_kinds",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("name_normalized", sa.String(100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("uq_lesson_kind_name_normalized", "lesson_kinds", ["name_normalized"], unique=True)

    # 2. Seed initial lesson kinds
    op.execute("""
        INSERT INTO lesson_kinds (id, name, name_normalized, created_at, updated_at)
        VALUES
            (uuid_generate_v4(), 'Beginner', 'beginner', NOW(), NOW()),
            (uuid_generate_v4(), 'Elementary', 'elementary', NOW(), NOW()),
            (uuid_generate_v4(), 'Intermediate', 'intermediate', NOW(), NOW()),
            (uuid_generate_v4(), 'Advanced', 'advanced', NOW(), NOW())
    """)

    # 3. Add tuition_fee_per_lesson to class_sessions (nullable for existing rows)
    op.add_column("class_sessions", sa.Column("tuition_fee_per_lesson", sa.BigInteger(), nullable=True))
    op.add_column("class_sessions", sa.Column("lesson_kind_id", UUID(as_uuid=True), sa.ForeignKey("lesson_kinds.id"), nullable=True))
    op.create_index("ix_class_sessions_lesson_kind_id", "class_sessions", ["lesson_kind_id"])
    op.execute("""
        ALTER TABLE class_sessions
        ADD CONSTRAINT ck_class_sessions_fee_positive
        CHECK (tuition_fee_per_lesson IS NULL OR (tuition_fee_per_lesson > 0 AND tuition_fee_per_lesson <= 100000000))
    """)

    # 4. Drop skill_level from students
    op.drop_index("ix_students_skill_level", table_name="students", if_exists=True)
    op.drop_column("students", "skill_level")

    # 5. Drop dependent tables (FK order: renewal_reminders → payment_records → packages)
    op.execute("UPDATE attendance_records SET package_id = NULL")
    op.drop_constraint("attendance_records_package_id_fkey", "attendance_records", type_="foreignkey")
    op.drop_table("renewal_reminders")
    op.drop_table("payment_records")
    op.drop_table("packages")

    # 6. Recreate packages with new schema
    op.create_table(
        "packages",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("uuid_generate_v4()"), nullable=False),
        sa.Column("student_id", UUID(as_uuid=True), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("class_session_id", UUID(as_uuid=True), sa.ForeignKey("class_sessions.id"), nullable=False),
        sa.Column("number_of_lessons", sa.Integer(), nullable=False),
        sa.Column("remaining_sessions", sa.Integer(), nullable=False),
        sa.Column("price", sa.BigInteger(), nullable=False),
        sa.Column("payment_status", sa.String(20), server_default="unpaid", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("reminder_status", sa.String(20), server_default="none", nullable=False),
        sa.Column("started_at", sa.Date(), nullable=False),
        sa.Column("expired_at", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("number_of_lessons > 0 AND number_of_lessons <= 500", name="ck_packages_lessons_range"),
        sa.CheckConstraint("price > 0 AND price <= 1000000000", name="ck_packages_price_range"),
    )
    op.create_index("ix_packages_student_id", "packages", ["student_id"])
    op.create_index("ix_packages_class_session_id", "packages", ["class_session_id"])
    op.create_index("ix_packages_payment_status", "packages", ["payment_status"])
    op.create_index("ix_packages_is_active", "packages", ["is_active"])

    # Recreate FK for attendance_records
    op.create_foreign_key("attendance_records_package_id_fkey", "attendance_records", "packages", ["package_id"], ["id"])

    # 7. Recreate payment_records (same schema, FK to new packages)
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

    # 8. Recreate renewal_reminders (same schema, FK to new packages)
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
    # Reverse order: drop new tables, recreate old ones
    op.execute("UPDATE attendance_records SET package_id = NULL")
    op.drop_constraint("attendance_records_package_id_fkey", "attendance_records", type_="foreignkey")
    op.drop_table("renewal_reminders")
    op.drop_table("payment_records")
    op.drop_table("packages")

    # Recreate old packages table
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

    op.create_foreign_key("attendance_records_package_id_fkey", "attendance_records", "packages", ["package_id"], ["id"])

    # Recreate old payment_records
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

    # Recreate old renewal_reminders
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

    # Re-add skill_level to students
    op.add_column("students", sa.Column("skill_level", sa.String(50), nullable=False, server_default="beginner"))
    op.create_index("ix_students_skill_level", "students", ["skill_level"])

    # Drop tuition_fee_per_lesson and lesson_kind_id from class_sessions
    op.execute("ALTER TABLE class_sessions DROP CONSTRAINT IF EXISTS ck_class_sessions_fee_positive")
    op.drop_column("class_sessions", "tuition_fee_per_lesson")
    op.drop_index("ix_class_sessions_lesson_kind_id", table_name="class_sessions")
    op.drop_constraint("class_sessions_lesson_kind_id_fkey", "class_sessions", type_="foreignkey")
    op.drop_column("class_sessions", "lesson_kind_id")

    # Drop lesson_kinds
    op.drop_index("uq_lesson_kind_name_normalized", table_name="lesson_kinds")
    op.drop_table("lesson_kinds")
