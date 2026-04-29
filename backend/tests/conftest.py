"""Shared pytest fixtures.

Boots a Postgres container (via testcontainers), runs Alembic migrations against it,
and exposes an ``AsyncClient`` wired to the FastAPI app for integration tests.

If Docker is not available, tests requiring the ``client`` fixture will be skipped
rather than failing the whole suite.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from datetime import date
from uuid import uuid4

import pytest
import pytest_asyncio


@pytest.fixture(scope="session")
def event_loop():
    """Session-scoped event loop so async fixtures can share state."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def pg_url() -> str:
    """Boot a Postgres container and return an asyncpg URL."""
    try:
        from testcontainers.postgres import PostgresContainer
    except Exception as e:  # pragma: no cover
        pytest.skip(f"testcontainers not available: {e}")

    try:
        pg = PostgresContainer("postgres:16-alpine")
        pg.start()
    except Exception as e:  # Docker not running, etc.
        pytest.skip(f"Could not start postgres container: {e}")

    sync_url = pg.get_connection_url()  # postgresql+psycopg2://...
    async_url = sync_url.replace("postgresql+psycopg2://", "postgresql+asyncpg://").replace(
        "postgresql://", "postgresql+asyncpg://"
    )

    yield async_url

    pg.stop()


@pytest_asyncio.fixture(scope="session")
async def db_engine(pg_url: str):
    """Apply Alembic migrations on the test DB and yield an async engine."""
    import os

    os.environ["DATABASE_URL"] = pg_url
    # Reload settings so the rest of the app picks up the test URL.
    from app.core import config as _config

    _config.settings = _config.Settings()  # type: ignore[attr-defined]

    from alembic.config import Config as AlembicConfig

    from alembic import command

    alembic_cfg = AlembicConfig("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", pg_url)

    # Run migrations in a thread because alembic uses its own asyncio loop.
    await asyncio.to_thread(command.upgrade, alembic_cfg, "head")

    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(pg_url, future=True)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncIterator:
    """Per-test DB session, rolled back at the end of the test."""
    from sqlalchemy.ext.asyncio import async_sessionmaker

    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_engine) -> AsyncIterator:
    """HTTP client bound to the FastAPI app with the test DB engine."""
    from httpx import ASGITransport, AsyncClient
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from app.core.deps import get_db
    from app.main import app

    session_factory = async_sessionmaker(db_engine, expire_on_commit=False)

    async def _override_get_db():
        async with session_factory() as session:
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
    """Factory that creates a Center row and returns it."""
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
    """Factory that creates an admin User scoped to the given center."""
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
    """Login helper returning a Bearer-auth header dict."""

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
    """Factory that creates a Student in a given center."""
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
    """Factory that creates a Teacher in a given center."""
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
    """Factory that creates a ClassSession in a given center."""
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
