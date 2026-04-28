"""student contact

Revision ID: 010
Revises: 009
Create Date: 2026-04-27 00:00:00.000000

"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add contact JSONB NULL to students
    op.add_column("students", sa.Column("contact", postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    # Migrate data
    op.execute("""
        UPDATE students s
        SET contact = jsonb_build_object(
            'name', p.full_name,
            'relationship', 'parent',
            'phone', p.phone,
            'phone_secondary', p.phone_secondary,
            'email', null,
            'address', p.address,
            'zalo_id', p.zalo_id,
            'notes', p.notes
        )
        FROM parents p
        WHERE p.id = s.parent_id
    """)

    # Drop index, constraint, and column
    op.drop_index("ix_students_parent_id", table_name="students")
    op.drop_constraint("students_parent_id_fkey", "students", type_="foreignkey")
    op.drop_column("students", "parent_id")


def downgrade() -> None:
    # Add back parent_id column
    op.add_column("students", sa.Column("parent_id", postgresql.UUID(as_uuid=True), autoincrement=False, nullable=True))
    op.create_foreign_key("students_parent_id_fkey", "students", "parents", ["parent_id"], ["id"])
    op.create_index("ix_students_parent_id", "students", ["parent_id"], unique=False)

    # Drop contact column
    op.drop_column("students", "contact")
