"""Shared pytest fixtures.

Connects to a Postgres instance and exposes an ``AsyncClient`` wired to the
FastAPI app for integration tests. Each test runs inside a savepoint that is
rolled back at the end, so the DB ends up unchanged.

Resolution order for the test DB URL:

1. ``TEST_DATABASE_URL`` env var (e.g. an already-migrated dev DB)
2. ``testcontainers[postgres]`` if Docker is available
3. Skip — tests are skipped rather than failing the whole suite
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator
from datetime import date
from uuid import uuid4

import pytest
import pytest_asyncio


@pytest.fixture(scope="session")
def pg_url() -> str:
    """Resolve a Postgres URL for tests, preferring TEST_DATABASE_URL."""
    env_url = os.environ.get("TEST_DATABASE_URL")
    if env_url:
        yield env_url
        return

    try:
        from testcontainers.postgres import PostgresContainer
    except Exception as e:
        pytest.skip(f"testcontainers not available and TEST_DATABASE_URL unset: {e}")

    try:
        pg = PostgresContainer("postgres:16-alpine")
        pg.start()
    except Exception as e:
        pytest.skip(f"Could not start postgres container and TEST_DATABASE_URL unset: {e}")

    sync_url = pg.get_connection_url()
    async_url = sync_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://").replace(
        "postgresql://", "postgresql+asyncpg://"
    )
    yield async_url
    pg.stop()


@pytest_asyncio.fixture(scope="session")
async def db_engine(pg_url: str):
    """Async engine pointed at the test DB.

    When ``TEST_DATABASE_URL`` is set we trust the schema is already at head
    (typical for the dev DB). Otherwise we run Alembic migrations against the
    container we just started.
    """
    os.environ["DATABASE_URL"] = pg_url
    from app.core import config as _config

    _config.settings = _config.Settings()  # type: ignore[attr-defined]

    if not os.environ.get("TEST_DATABASE_URL"):
        from alembic.config import Config as AlembicConfig

        from alembic import command

        alembic_cfg = AlembicConfig("alembic.ini")
        alembic_cfg.set_main_option("sqlalchemy.url", pg_url)
        await asyncio.to_thread(command.upgrade, alembic_cfg, "head")

    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(pg_url, future=True)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_connection(db_engine):
    """Per-test connection with an outer transaction that gets rolled back."""
    async with db_engine.connect() as conn:
        trans = await conn.begin()
        try:
            yield conn
        finally:
            await trans.rollback()


@pytest_asyncio.fixture
async def db_session(db_connection) -> AsyncIterator:
    """Session bound to the per-test connection. Uses SAVEPOINTs so calls to
    ``commit()`` inside the app don't actually commit — they end the savepoint
    only, and the outer rollback nukes everything at test end."""
    from sqlalchemy.ext.asyncio import AsyncSession

    session = AsyncSession(bind=db_connection, expire_on_commit=False, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        await session.close()


@pytest_asyncio.fixture
async def client(db_connection) -> AsyncIterator:
    """HTTP client bound to the FastAPI app, sharing the rolled-back connection."""
    from httpx import ASGITransport, AsyncClient
    from sqlalchemy.ext.asyncio import AsyncSession

    from app.core.deps import get_db
    from app.main import app

    async def _override_get_db():
        session = AsyncSession(
            bind=db_connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )
        try:
            yield session
        finally:
            await session.close()

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.pop(get_db, None)


# ── Factory helpers ────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def make_center(db_session):
    from app.models.center import Center

    async def _make(name: str | None = None, code: str | None = None, is_active: bool = True):
        suffix = uuid4().hex[:8]
        c = Center(
            name=name or f"Center-{suffix}",
            code=code or f"C{suffix.upper()}",
            is_active=is_active,
        )
        db_session.add(c)
        await db_session.commit()
        await db_session.refresh(c)
        return c

    return _make


@pytest_asyncio.fixture
async def make_admin(db_session):
    from app.core.security import hash_password
    from app.models.user import User

    async def _make(center, *, username: str | None = None, password: str = "secret123"):
        suffix = uuid4().hex[:8]
        u = User(
            username=username or f"admin-{suffix}",
            password_hash=hash_password(password),
            role="admin",
            full_name="Test Admin",
            language="en",
            center_id=center.id,
            is_active=True,
        )
        db_session.add(u)
        await db_session.commit()
        await db_session.refresh(u)
        u._plain_password = password  # type: ignore[attr-defined]
        return u

    return _make


@pytest_asyncio.fixture
async def login(client):
    async def _login(user) -> dict[str, str]:
        password = getattr(user, "_plain_password", "secret123")
        resp = await client.post(
            "/api/v1/auth/login",
            json={"username": user.username, "password": password},
        )
        assert resp.status_code == 200, resp.text
        token = resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    return _login


@pytest_asyncio.fixture
async def make_student(db_session):
    from app.models.student import Student

    async def _make(center, name: str = "Student"):
        s = Student(
            name=f"{name}-{uuid4().hex[:6]}",
            enrolled_at=date.today(),
            center_id=center.id,
        )
        db_session.add(s)
        await db_session.commit()
        await db_session.refresh(s)
        return s

    return _make


@pytest_asyncio.fixture
async def make_teacher(db_session):
    from app.models.teacher import Teacher

    async def _make(center, name: str = "Teacher"):
        t = Teacher(
            full_name=f"{name}-{uuid4().hex[:6]}",
            center_id=center.id,
        )
        db_session.add(t)
        await db_session.commit()
        await db_session.refresh(t)
        return t

    return _make


@pytest_asyncio.fixture
async def make_class(db_session):
    from datetime import time

    from app.models.class_session import ClassSession

    async def _make(
        center,
        teacher,
        *,
        day_of_week: int = 1,
        start_time: str = "09:00",
        duration_minutes: int = 60,
        name: str = "Class",
    ):
        cs = ClassSession(
            teacher_id=teacher.id,
            name=f"{name}-{uuid4().hex[:6]}",
            day_of_week=day_of_week,
            start_time=time.fromisoformat(start_time),
            duration_minutes=duration_minutes,
            is_recurring=True,
            recurring_pattern="weekly",
            center_id=center.id,
        )
        db_session.add(cs)
        await db_session.commit()
        await db_session.refresh(cs)
        return cs

    return _make
