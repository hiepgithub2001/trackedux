"""Add charge_fee column to attendance_records

Revision ID: 018
Revises: 017
Create Date: 2026-04-29

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "018"
down_revision: str | None = "017"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Add charge_fee column with server default true
    op.add_column(
        "attendance_records",
        sa.Column("charge_fee", sa.Boolean(), nullable=False, server_default="true"),
    )
    # Backfill: set charge_fee=false for records that were not 'present'
    # (preserves the old behavior where only present students were charged)
    op.execute("UPDATE attendance_records SET charge_fee = false WHERE status != 'present'")


def downgrade() -> None:
    op.drop_column("attendance_records", "charge_fee")
