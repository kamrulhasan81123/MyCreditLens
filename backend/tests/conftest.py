import os

# Pin the test suite to a lightweight local SQLite database, regardless of the
# .env DATABASE_URL (which may point at Supabase Postgres for the running app).
# Environment variables override the .env file in pydantic-settings, and this
# MUST run before app.config is first imported below.
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./_pytest_lifespan.db"
os.environ["DATABASE_URL_SYNC"] = "sqlite:///./_pytest_lifespan.db"
os.environ["APP_ENV"] = "test"
# Keep the offline unit suite hermetic: disable live Supabase Storage so
# data-source uploads use the local fallback (live storage is covered by the
# opt-in tests/test_supabase_integration.py).
os.environ["SUPABASE_SECRET_KEY"] = ""

import asyncio
from collections.abc import AsyncIterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.database import Base, get_db
from app.main import app


@pytest.fixture()
def client(tmp_path) -> AsyncIterator[TestClient]:
    database_path = tmp_path / "test.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{database_path}")
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def prepare() -> None:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    asyncio.run(prepare())
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        test_client.session_factory = session_factory
        yield test_client
    app.dependency_overrides.clear()
    asyncio.run(engine.dispose())
