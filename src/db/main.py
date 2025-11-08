# Database connection and initialization (Async)
import sys
import asyncio
import logging
from typing import AsyncGenerator
import sqlalchemy as sa

# Ensure Windows compatibility for psycopg
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession
from src.logger import setup_logger
from src.config import Config as settings

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
    pool_pre_ping=True,  # Test connections before using them
    pool_size=5,  # Maximum number of connections to keep in pool
    max_overflow=10,  # Maximum overflow size for connection pool
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_timeout=30,  # Timeout for getting connection from pool
    connect_args={
        "options": "-c application_name=bedrock-backend",
        "connect_timeout": 10,  # Connection timeout in seconds
    }
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
    """Initialize database tables with timeout protection"""
    try:
        logger.info("Initializing database tables...")
        # Add timeout to prevent indefinite hanging
        async with asyncio.timeout(30):  # 30 second timeout
            async with engine.begin() as conn:
                await conn.run_sync(SQLModel.metadata.create_all)
        logger.info("Database tables initialized successfully")
    except asyncio.TimeoutError:
        logger.error("Database initialization timed out after 30 seconds")
        logger.error("This usually means the database is unreachable or slow")
        raise
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}", exc_info=True)
        raise


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session dependency for FastAPI"""
    logger.debug("Creating new async database session...")
    
    async with SessionLocal() as session:
        try:
            logger.debug(f"Async session created: {id(session)}")
            yield session
            logger.debug(f"Async session {id(session)} yielded successfully")
            await session.commit()
        except Exception as e:
            logger.error(f"Error during session usage: {str(e)}", exc_info=True)
            logger.error(f"Session ID: {id(session)}")
            await session.rollback()
            raise
        finally:
            await session.close()

