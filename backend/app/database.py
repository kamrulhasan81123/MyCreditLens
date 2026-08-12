from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text, event
from app.config import get_settings

settings = get_settings()

_IS_SQLITE = "sqlite" in settings.database_url

_engine_kwargs: dict[str, Any] = {"echo": settings.debug}
if _IS_SQLITE:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    _engine_kwargs["pool_size"] = 5
    _engine_kwargs["max_overflow"] = 5
    _engine_kwargs["pool_pre_ping"] = True
    _engine_kwargs["pool_recycle"] = 1800
    # Supabase (and the Supavisor pooler) require TLS. asyncpg verifies the CA by
    # default, but the pooler presents a chain that isn't in the system store, so
    # use require-mode TLS (encrypt, skip CA verification) — equivalent to
    # sslmode=require, which Supabase documents for these hosts.
    if "asyncpg" in settings.database_url:
        import ssl

        _ssl_ctx = ssl.create_default_context()
        _ssl_ctx.check_hostname = False
        _ssl_ctx.verify_mode = ssl.CERT_NONE
        _engine_kwargs["connect_args"] = {"ssl": _ssl_ctx}

engine = create_async_engine(settings.database_url, **_engine_kwargs)


@event.listens_for(engine.sync_engine, "connect")
def _sqlite_pragma(dbapi_connection, connection_record):
    if _IS_SQLITE:
        import sqlite3
        if isinstance(dbapi_connection, sqlite3.Connection):
            dbapi_connection.execute("PRAGMA journal_mode=WAL")
            dbapi_connection.execute("PRAGMA foreign_keys=ON")


async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    import app.models  # noqa: F401 - ensure all model metadata is registered

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def validate_database_connection() -> bool:
    async with engine.connect() as conn:
        await conn.execute(text("select 1"))
    return True
