"""
Async SQLAlchemy database configuration and session management.

This module sets up the async SQLite engine and provides dependency
injection for database sessions in FastAPI endpoints.
"""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Declarative base for all models
Base = declarative_base()

# Global engine and session factory
engine: AsyncEngine | None = None
async_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """
    Get or create the async database engine.
    
    Returns:
        AsyncEngine instance configured for SQLite
    """
    global engine
    if engine is None:
        database_url = settings.get_database_url()
        engine = create_async_engine(
            database_url,
            echo=settings.debug,
            future=True,
            # SQLite-specific optimizations
            connect_args={"check_same_thread": False}
        )
        logger.info(f"Database engine created: {database_url}")
    return engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Get or create the async session factory.
    
    Returns:
        Session factory for creating database sessions
    """
    global async_session_factory
    if async_session_factory is None:
        async_session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
        logger.info("Session factory created")
    return async_session_factory


async def init_db() -> None:
    """
    Initialize the database schema.
    
    Creates all tables defined in SQLAlchemy models.
    Should be called on application startup.
    """
    logger.info("Initializing database schema...")
    
    # Import all models to ensure they're registered
    from app.models import bot, credential, log  # noqa: F401
    
    async with get_engine().begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database schema initialized successfully")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI endpoints to get database sessions.
    
    Yields:
        AsyncSession that automatically commits or rolls back
        
    Example:
        @app.get("/bots")
        async def list_bots(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Bot))
            return result.scalars().all()
    """
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_db() -> None:
    """
    Close database connections.
    
    Should be called on application shutdown.
    """
    global engine
    if engine is not None:
        await engine.dispose()
        logger.info("Database connections closed")
