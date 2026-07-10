"""Async engine/session plumbing. Lazy so importing the app never connects."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings

from .models import Base

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def configure(url: str | None = None) -> None:
    """(Re)point persistence at a database. Tests call this with SQLite."""
    global _engine, _session_factory
    _engine = create_async_engine(url or settings.database_url)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)


def session_factory() -> async_sessionmaker[AsyncSession]:
    if _session_factory is None:
        configure()
    assert _session_factory is not None
    return _session_factory


async def create_tables() -> None:
    if _engine is None:
        configure()
    assert _engine is not None
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def dispose() -> None:
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None
