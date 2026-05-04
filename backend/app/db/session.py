"""Database engine and async session factory."""

import ssl
from urllib.parse import parse_qs, urlparse, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

def get_engine_args(url: str):
    connect_args = {}
    if url and "sslmode=" in url:
        parsed_url = urlparse(url)
        query = parse_qs(parsed_url.query)
        query.pop('sslmode', None)
        query.pop('channel_binding', None)
        new_query = '&'.join([f"{k}={v[0]}" for k, v in query.items()])
        url = urlunparse(parsed_url._replace(query=new_query))
        
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        connect_args["ssl"] = ctx
    return url, connect_args

db_url, db_connect_args = get_engine_args(settings.DATABASE_URL)

engine = create_async_engine(
    db_url,
    connect_args=db_connect_args,
    echo=False,
    pool_size=10,
    max_overflow=20,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
