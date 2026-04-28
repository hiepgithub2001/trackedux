"""Tuition revamp: drop packages/payment_records, create tuition tables, modify attendance/students.

Revision ID: 016
Revises: 015
Create Date: 2026-04-28

"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '016'
down_revision: str | None = '015'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- 1. Drop FK constraint attendance_records.package_id → packages ---
    op.drop_constraint('attendance_records_package_id_fkey', 'attendance_records', type_='foreignkey')
    op.drop_column('attendance_records', 'package_id')

    # --- 2. Drop renewal_reminders (references packages) ---
    op.drop_table('renewal_reminders')

    # --- 3. Drop payment_records (references packages) ---
    op.drop_table('payment_records')

    # --- 4. Drop packages ---
    op.drop_table('packages')

    # --- 5. Add balance column to students ---
    op.add_column('students', sa.Column('balance', sa.BigInteger(), nullable=False, server_default='0'))

    # --- 6. Create tuition_payments table ---
    op.create_table(
        'tuition_payments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('students.id'), nullable=False),
        sa.Column('amount', sa.BigInteger(), nullable=False),
        sa.Column('payment_date', sa.Date(), nullable=False),
        sa.Column('payment_method', sa.String(50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('recorded_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('center_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('centers.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_tuition_payments_student_id', 'tuition_payments', ['student_id'])
    op.create_index('ix_tuition_payments_center_id', 'tuition_payments', ['center_id'])
    op.create_index('ix_tuition_payments_payment_date', 'tuition_payments', ['payment_date'])

    # --- 7. Create tuition_ledger_entries table ---
    op.create_table(
        'tuition_ledger_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('students.id'), nullable=False),
        sa.Column('entry_type', sa.String(20), nullable=False),
        sa.Column('amount', sa.BigInteger(), nullable=False),
        sa.Column('balance_after', sa.BigInteger(), nullable=False),
        sa.Column('payment_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tuition_payments.id'), nullable=True),
        sa.Column('attendance_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('attendance_records.id'), nullable=True),
        sa.Column('class_session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('class_sessions.id'), nullable=True),
        sa.Column('entry_date', sa.Date(), nullable=False),
        sa.Column('description', sa.String(200), nullable=False),
        sa.Column('center_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('centers.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_ledger_student_created', 'tuition_ledger_entries', ['student_id', 'created_at'])
    op.create_index('ix_ledger_center', 'tuition_ledger_entries', ['center_id'])
    op.create_index('ix_ledger_entry_date', 'tuition_ledger_entries', ['entry_date'])
    # Partial unique index: prevent duplicate deductions for the same attendance record
    op.create_index(
        'ix_ledger_attendance_unique',
        'tuition_ledger_entries',
        ['attendance_id'],
        unique=True,
        postgresql_where=sa.text('attendance_id IS NOT NULL'),
    )


def downgrade() -> None:
    # Drop new tables
    op.drop_table('tuition_ledger_entries')
    op.drop_table('tuition_payments')

    # Remove balance from students
    op.drop_column('students', 'balance')

    # Recreate packages table (simplified — for rollback only)
    op.create_table(
        'packages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('students.id'), nullable=False),
        sa.Column('class_session_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('class_sessions.id'), nullable=False),
        sa.Column('number_of_lessons', sa.Integer(), nullable=False),
        sa.Column('remaining_sessions', sa.Integer(), nullable=False),
        sa.Column('price', sa.BigInteger(), nullable=True),
        sa.Column('payment_status', sa.String(20), nullable=False, server_default='unpaid'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('reminder_status', sa.String(30), nullable=False, server_default='none'),
        sa.Column('center_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('centers.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Recreate payment_records (simplified — for rollback only)
    op.create_table(
        'payment_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('package_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('packages.id'), nullable=False),
        sa.Column('amount', sa.BigInteger(), nullable=False),
        sa.Column('payment_date', sa.Date(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('center_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('centers.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # Recreate renewal_reminders (simplified — for rollback only)
    op.create_table(
        'renewal_reminders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('package_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('packages.id'), nullable=False),
        sa.Column('reminder_number', sa.Integer(), nullable=False),
        sa.Column('triggered_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('notification_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('center_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('centers.id'), nullable=False),
    )

    # Re-add package_id to attendance_records
    op.add_column('attendance_records', sa.Column('package_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('attendance_records_package_id_fkey', 'attendance_records', 'packages', ['package_id'], ['id'])
