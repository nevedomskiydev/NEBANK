"""Async SQLAlchemy engine, session factory and Base."""
from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

_engine_kwargs: dict = {"echo": False, "pool_pre_ping": True}
if not settings.database_url.startswith("sqlite"):
    _engine_kwargs.update(pool_size=20, max_overflow=40, pool_recycle=1800)

engine = create_async_engine(settings.database_url, **_engine_kwargs)

SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency."""
    async with SessionLocal() as session:
        yield session
