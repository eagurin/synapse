"""Database configuration and session management"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.core.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.ENVIRONMENT == "development",
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Create base class for models
Base = declarative_base()


async def get_db() -> AsyncSession:
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database"""
    # Create schemas
    async with engine.begin() as conn:
        await conn.execute("CREATE SCHEMA IF NOT EXISTS r2r")
        await conn.execute("CREATE SCHEMA IF NOT EXISTS mem0")
        await conn.execute("CREATE SCHEMA IF NOT EXISTS shared")
        
        # TODO: Run alembic migrations
        # For now, just ensure extensions
        await conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        await conn.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
        await conn.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')