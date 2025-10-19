"""
Database connection and session management.
Uses async SQLAlchemy for optimal performance.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from .config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,  # Verify connections before using
)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Base class for ORM models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """
    Dependency to get async database session.

    Usage:
        @router.get("/batches")
        async def get_batches(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
