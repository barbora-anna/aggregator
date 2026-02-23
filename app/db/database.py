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

# Module-level state, set during app lifespan
engine: AsyncEngine | None = None
session_factory: async_sessionmaker[AsyncSession] | None = None


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
    """Manage lifetime of database engine and session factory."""
    global session_factory
    log.info("Connecting to database...")
    eng = make_engine()
    session_factory = make_session_factory(eng)
    try:
        yield eng
    finally:
        log.info("Disposing database connection")
        session_factory = None
        await eng.dispose()


@asynccontextmanager
async def db_session() -> t.AsyncIterator[AsyncSession]:
    """Acquire ORM session with automatic transaction management."""
    if session_factory is None:
        raise RuntimeError("Database not initialized")
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_session() -> t.AsyncIterator[AsyncSession]:
    """FastAPI dependency that yields a database session."""
    async with db_session() as session:
        yield session
