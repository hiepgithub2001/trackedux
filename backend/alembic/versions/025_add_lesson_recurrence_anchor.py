"""add recurrence_anchor to lessons

Revision ID: 025
Revises: 024
Create Date: 2026-07-12 05:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "025"
down_revision: str | None = "024"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Effective-from anchor for the lesson's RRULE. When null, expansion falls back
    # to created_at. Set forward on a schedule edit so a changed recurrence never
    # retroactively spawns past occurrences.
    op.add_column("lessons", sa.Column("recurrence_anchor", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("lessons", "recurrence_anchor")
