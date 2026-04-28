"""Drop class_type and max_students; add name and duration_minutes.

Revision ID: 009
Revises: 008
Create Date: 2026-04-27

Aligns the ClassSession schema with the 2026-04-27 clarification:
- No class type classification (1:1 / pair / group removed)
- No max_students upper bound
- Class has a required `name`
- Duration is stored explicitly as `duration_minutes` (replaces `end_time`)
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "009"
down_revision: str | None = "008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Add `name` (nullable first so we can backfill from `title`).
    op.add_column("class_sessions", sa.Column("name", sa.String(200), nullable=True))
    op.execute("UPDATE class_sessions SET name = COALESCE(NULLIF(title, ''), 'Untitled class')")
    op.alter_column("class_sessions", "name", nullable=False)

    # 2. Add `duration_minutes` (nullable first so we can backfill from end_time - start_time).
    op.add_column("class_sessions", sa.Column("duration_minutes", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE class_sessions
        SET duration_minutes = GREATEST(
            1,
            CAST(EXTRACT(EPOCH FROM (end_time - start_time)) / 60 AS INTEGER)
        )
        """
    )
    op.alter_column("class_sessions", "duration_minutes", nullable=False)
    op.create_check_constraint(
        "ck_class_sessions_duration_positive",
        "class_sessions",
        "duration_minutes > 0",
    )

    # 3. Drop the now-obsolete columns.
    op.drop_column("class_sessions", "class_type")
    op.drop_column("class_sessions", "max_students")
    op.drop_column("class_sessions", "title")
    op.drop_column("class_sessions", "end_time")

    # 4. Drop the orphaned class_type enum type created in migration 002.
    #    No column references it after step 3, so this is safe.
    op.execute("DROP TYPE IF EXISTS class_type")


def downgrade() -> None:
    # Recreate the orphaned enum type before any column might reference it.
    op.execute("CREATE TYPE class_type AS ENUM ('individual', 'pair', 'group')")

    # Restore the legacy columns. Defaults pick safe-but-arbitrary values; the
    # original data is not recoverable.
    op.add_column(
        "class_sessions",
        sa.Column("class_type", sa.String(20), nullable=False, server_default="group"),
    )
    op.add_column(
        "class_sessions",
        sa.Column("max_students", sa.Integer(), nullable=False, server_default="4"),
    )
    op.add_column("class_sessions", sa.Column("title", sa.String(200), nullable=True))
    op.execute("UPDATE class_sessions SET title = name")
    op.add_column("class_sessions", sa.Column("end_time", sa.Time(), nullable=True))
    op.execute("UPDATE class_sessions SET end_time = (start_time + (duration_minutes || ' minutes')::interval)::time")
    op.alter_column("class_sessions", "end_time", nullable=False)

    op.drop_constraint("ck_class_sessions_duration_positive", "class_sessions", type_="check")
    op.drop_column("class_sessions", "duration_minutes")
    op.drop_column("class_sessions", "name")

    # Strip server defaults that were only there to satisfy the backfill.
    op.alter_column("class_sessions", "class_type", server_default=None)
    op.alter_column("class_sessions", "max_students", server_default=None)
