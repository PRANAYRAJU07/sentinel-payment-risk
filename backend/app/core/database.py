"""
Sentinel Backend — Database Connection
Async SQLAlchemy with PostgreSQL via asyncpg.
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import get_settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


def get_engine():
    settings = get_settings()
    return create_async_engine(
        settings.database_url,
        echo=settings.app_debug,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
    )


def get_session_factory(engine):
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


# Module-level engine and session factory (lazy init)
_engine = None
_session_factory = None


def get_db_engine():
    global _engine
    if _engine is None:
        _engine = get_engine()
    return _engine


def get_db_session_factory():
    global _session_factory
    if _session_factory is None:
        _session_factory = get_session_factory(get_db_engine())
    return _session_factory


async def get_db() -> AsyncSession:
    """FastAPI dependency: yields a database session."""
    session_factory = get_db_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
