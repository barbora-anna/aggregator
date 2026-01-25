"""Postgres connection tooling."""

import logging
import typing as t
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

log = logging.getLogger(__name__)

# Module-level engine, set during app lifespan
engine: AsyncEngine | None = None


def make_engine() -> AsyncEngine:
    """Create async database engine."""
    return create_async_engine(settings.database_url)


def make_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create session factory for ORM operations."""
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


@asynccontextmanager
async def manage_db_engine() -> t.AsyncIterator[AsyncEngine]:
    """Manage lifetime of database engine."""
    log.info("Connecting to database...")
    engine = make_engine()
    try:
        yield engine
    finally:
        log.info("Disposing database connection")
        await engine.dispose()


@asynccontextmanager
async def db_session(engine: AsyncEngine) -> t.AsyncIterator[AsyncSession]:
    """Acquire ORM session with automatic transaction management."""
    session_factory = make_session_factory(engine)
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_session() -> t.AsyncIterator[AsyncSession]:
    """FastAPI dependency that yields a database session."""
    session_factory = make_session_factory(engine)
    async with session_factory() as session:
        yield session
