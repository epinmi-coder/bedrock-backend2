# Database connection and initialization (Async)
import logging
from typing import AsyncGenerator
import sqlalchemy as sa
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
from logger import setup_logger
from settings import settings

# Setup module logger with file and console handlers
logger = setup_logger(__name__)

logger.info("Initializing database configuration")

# Get database URL from settings (handles SSM, env vars, and SSL configuration)
db_url = settings.DATABASE_URL

# Production database configuration with async engine
logger.info("Creating async database engine...")
logger.debug(f"Echo SQL: True")

engine = create_async_engine(
    db_url,
    echo=True,  # SQL query logging for debugging
)

logger.info("Database engine created successfully")

# Session factory for async sessions
logger.debug("Configuring async session factory...")
SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False  # Prevent implicit flushing for better performance control
)
logger.info("Async session factory configured")

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session dependency for FastAPI"""
    logger.debug("Creating new async database session...")
    
    async with SessionLocal() as session:
        try:
            logger.debug(f"Async session created: {id(session)}")
            yield session
            logger.debug(f"Async session {id(session)} yielded successfully")
        except Exception as e:
            logger.error(f"Error during session usage: {str(e)}", exc_info=True)
            logger.error(f"Session ID: {id(session)}")
            await session.rollback()
            raise

