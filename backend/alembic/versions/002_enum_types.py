"""Create PostgreSQL enum types.

Revision ID: 002
Revises: 001
Create Date: 2026-04-27
"""

from collections.abc import Sequence

from alembic import op

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE TYPE user_role AS ENUM ('admin', 'staff', 'parent')")
    op.execute("CREATE TYPE enrollment_status AS ENUM ('trial', 'active', 'paused', 'withdrawn')")
    op.execute("CREATE TYPE class_type AS ENUM ('individual', 'pair', 'group')")
    op.execute("CREATE TYPE payment_status AS ENUM ('paid', 'unpaid')")
    op.execute("CREATE TYPE attendance_status AS ENUM ('present', 'absent', 'absent_with_notice')")
    op.execute(
        "CREATE TYPE notification_type AS ENUM ('schedule_reminder', 'payment_due', 'payment_overdue', 'renewal_reminder')"
    )
    op.execute("CREATE TYPE notification_channel AS ENUM ('zalo', 'sms')")
    op.execute("CREATE TYPE notification_status AS ENUM ('pending', 'sent', 'failed')")


def downgrade() -> None:
    op.execute("DROP TYPE IF EXISTS notification_status")
    op.execute("DROP TYPE IF EXISTS notification_channel")
    op.execute("DROP TYPE IF EXISTS notification_type")
    op.execute("DROP TYPE IF EXISTS attendance_status")
    op.execute("DROP TYPE IF EXISTS payment_status")
    op.execute("DROP TYPE IF EXISTS class_type")
    op.execute("DROP TYPE IF EXISTS enrollment_status")
    op.execute("DROP TYPE IF EXISTS user_role")
