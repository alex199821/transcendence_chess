from collections.abc import AsyncIterator

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# One engine per process. It holds a pool of reusable DB connections.
engine = create_async_engine(settings.database_url, pool_pre_ping=True)

# Factory that creates a new session (one unit of work / transaction) when called.
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

# Predictable names for indexes and constraints, so Alembic migrations stay stable.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Parent class for all models (tables)."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: opens a session for one request and always closes it after."""
    async with SessionLocal() as session:
        yield session