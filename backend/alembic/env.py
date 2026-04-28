"""Alembic async migration environment."""

import asyncio
import re
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from app.core.config import settings
from app.db.base import Base

# Import all models so Alembic can detect them
from app.models import *  # noqa: F401, F403

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def process_revision_directives(migration_context, revision, directives):
    """Generate sequential revision IDs (e.g. 015)."""
    # Extract the script
    script = directives[0]

    # Don't generate empty migrations for autogenerate
    if getattr(config.cmd_opts, "autogenerate", False):
        if script.upgrade_ops.is_empty():
            directives[:] = []
            return

    head_rev = migration_context.get_current_revision()
    if head_rev is None:
        new_rev_id = 1
    else:
        m = re.match(r'^(\d+)', head_rev)
        if m:
            new_rev_id = int(m.group(1)) + 1
        else:
            new_rev_id = 1

    script.rev_id = f'{new_rev_id:03d}'


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        process_revision_directives=process_revision_directives,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """Run migrations with the given connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        process_revision_directives=process_revision_directives,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' async mode."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
