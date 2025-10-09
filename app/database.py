"""
Database connection and models
"""

from typing import AsyncGenerator, Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, Session
from app.config import get_settings

settings = get_settings()

# Build database URLs directly
# Sync URL for Alembic migrations (uses psycopg2)
SYNC_DATABASE_URL = (
    f"postgresql://{settings.postgres_user}:{settings.postgres_password}"
    f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
)

# Async URL for FastAPI application (uses asyncpg)
ASYNC_DATABASE_URL = (
    f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}"
    f"@{settings.postgres_host}:{settings.postgres_port}/{settings.postgres_db}"
)

# Create async engine for PostgreSQL
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=settings.debug,
    future=True,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# Create sync engine for synchronous operations (used by Alembic)
sync_engine = create_engine(SYNC_DATABASE_URL, echo=settings.debug)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def get_sync_session() -> Generator[Session, None, None]:
    """
    Get synchronous database session
    """
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
