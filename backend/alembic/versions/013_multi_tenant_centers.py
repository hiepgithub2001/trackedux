"""013 multi_tenant_centers.

Revision ID: 013
Revises: 012
Create Date: 2026-04-28

Adds multi-tenancy support:
- Creates `centers` table
- Inserts legacy center (CTR-001) and migrates all existing rows
- Adds `center_id` FK to all tenant-scoped tables
- Adds `superadmin` role support to `users` (center_id nullable for superadmin)
- Seeds the superadmin user
"""

from __future__ import annotations

import secrets
import string
import uuid

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "013"
down_revision: str | None = "012"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None

LEGACY_CENTER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
SUPERADMIN_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")

# Tables that receive center_id (in order to avoid FK issues)
TENANT_TABLES = [
    "students",
    "teachers",
    "class_sessions",
    "class_enrollments",
    "packages",
    "payment_records",
    "attendance_records",
    "renewal_reminders",
    "lesson_kinds",
    "student_status_history",
]


def _hash_password(plain: str) -> str:
    """Bcrypt hash for seeding — mirrors app.core.security.hash_password."""
    from passlib.context import CryptContext
    ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
    return ctx.hash(plain)


def upgrade() -> None:
    # ── 1. Create centers table ──────────────────────────────────────────────
    op.create_table(
        "centers",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column("registered_by_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("name", name="uq_centers_name"),
        sa.UniqueConstraint("code", name="uq_centers_code"),
    )
    op.create_index("ix_centers_name", "centers", ["name"])
    op.create_index("ix_centers_code", "centers", ["code"])

    # FK from centers.registered_by_id → users.id added after users is modified
    # (we add it at the end to avoid circular FK issues during migration)

    # ── 2. Insert legacy center ──────────────────────────────────────────────
    op.execute(
        sa.text(
            "INSERT INTO centers (id, name, code, is_active, created_at, updated_at) "
            "VALUES (:id, :name, :code, true, now(), now())"
        ).bindparams(id=LEGACY_CENTER_ID, name="Legacy Center", code="CTR-001")
    )

    # ── 3. Add center_id to all tenant tables ────────────────────────────────
    for table in TENANT_TABLES:
        # Add nullable column
        op.add_column(table, sa.Column("center_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
        # Backfill existing rows to legacy center
        op.execute(
            sa.text(f"UPDATE {table} SET center_id = :cid").bindparams(cid=LEGACY_CENTER_ID)
        )
        # Make NOT NULL
        op.alter_column(table, "center_id", nullable=False)
        # Add FK constraint
        op.create_foreign_key(
            f"fk_{table}_center_id",
            table, "centers",
            ["center_id"], ["id"],
            ondelete="RESTRICT",
        )
        # Add index
        op.create_index(f"ix_{table}_center_id", table, ["center_id"])

    # ── 4. Add center_id to users ────────────────────────────────────────────
    op.add_column("users", sa.Column("center_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
    op.execute(
        sa.text("UPDATE users SET center_id = :cid").bindparams(cid=LEGACY_CENTER_ID)
    )
    # NOTE: center_id stays nullable for superadmin (role = 'superadmin') — enforced at app layer only
    op.create_foreign_key(
        "fk_users_center_id",
        "users", "centers",
        ["center_id"], ["id"],
        ondelete="RESTRICT",
    )
    op.create_index("ix_users_center_id", "users", ["center_id"])

    # ── 5. Add FK from centers → users (registered_by_id) ───────────────────
    op.create_foreign_key(
        "fk_centers_registered_by_id",
        "centers", "users",
        ["registered_by_id"], ["id"],
        ondelete="SET NULL",
    )

    # ── 6. Seed superadmin user ──────────────────────────────────────────────
    pw_hash = _hash_password("SuperAdmin@2026!")
    op.execute(
        sa.text(
            "INSERT INTO users (id, username, email, password_hash, role, full_name, language, is_active, center_id, created_at, updated_at) "
            "VALUES (:id, 'superadmin', 'superadmin@system.internal', :pw, 'superadmin', 'System Admin', 'vi', true, NULL, now(), now())"
        ).bindparams(id=SUPERADMIN_ID, pw=pw_hash)
    )


def downgrade() -> None:
    # Remove superadmin user
    op.execute(sa.text("DELETE FROM users WHERE id = :id").bindparams(id=SUPERADMIN_ID))

    # Drop FK from centers → users
    op.drop_constraint("fk_centers_registered_by_id", "centers", type_="foreignkey")

    # Remove center_id from users
    op.drop_index("ix_users_center_id", table_name="users")
    op.drop_constraint("fk_users_center_id", "users", type_="foreignkey")
    op.drop_column("users", "center_id")

    # Remove center_id from all tenant tables (reverse order)
    for table in reversed(TENANT_TABLES):
        op.drop_index(f"ix_{table}_center_id", table_name=table)
        op.drop_constraint(f"fk_{table}_center_id", table, type_="foreignkey")
        op.drop_column(table, "center_id")

    # Drop indexes and centers table
    op.drop_index("ix_centers_code", table_name="centers")
    op.drop_index("ix_centers_name", table_name="centers")
    op.drop_table("centers")
