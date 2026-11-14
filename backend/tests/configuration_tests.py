import asyncio

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import make_url, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import settings
from app.db import Base, get_session
from app.main import app

# Tests use their own database ("chess" -> "chess_test"), so your real data is never touched.
real_url = make_url(settings.database_url)
test_url = real_url.set(database=f"{real_url.database}_test")

engine = create_async_engine(test_url, poolclass=NullPool)
TestSession = async_sessionmaker(engine, expire_on_commit=False)


async def create_test_database() -> None:
    admin = create_async_engine(real_url, isolation_level="AUTOCOMMIT", poolclass=NullPool)
    async with admin.connect() as conn:
        exists = await conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": test_url.database}
        )
        if not exists:
            await conn.execute(text(f'CREATE DATABASE "{test_url.database}"'))
    await admin.dispose()


async def empty_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def get_test_session():
    async with TestSession() as session:
        yield session


# Every endpoint that asks for get_session gets a test-database session instead.
app.dependency_overrides[get_session] = get_test_session

asyncio.run(create_test_database())


@pytest.fixture
def client():
    """A fake browser: sends requests straight to our app and keeps cookies. Fresh tables each test."""
    asyncio.run(empty_tables())
    with TestClient(app, base_url="https://testserver") as c:
        yield c