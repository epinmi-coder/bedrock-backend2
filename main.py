# Main FastAPI application with clean lifecycle management
import sys
import locale

import asyncio
import selectors

# Force Windows to use SelectorEventLoop for psycopg compatibility
if sys.platform == "win32":
    # Use the exact solution suggested by psycopg error message
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    # Set UTF-8 encoding for Windows console
    try:
        # Set console to UTF-8
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleCP(65001)  # UTF-8 input
        kernel32.SetConsoleOutputCP(65001)  # UTF-8 output
    except Exception:
        pass  # Ignore if it fails
    
    # Set locale for proper encoding
    try:
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except Exception:
        pass  # Ignore if locale not available

import os
import uvicorn
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.auth.routes import auth_router
from src.chats.routes import chat_router
from src.history.routes import history_router
from src.config_routes.routes import config_router
from src.db.main import init_db
from src.middleware import register_middleware
from src.config import Config as settings
from src.logger import setup_logger

# Configure logging
logger = setup_logger(__name__)
logger.setLevel(settings.LOG_LEVEL)

version = "v1"

version_prefix = f"/api/{version}"

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager for database and services."""
    # Startup
    logger.info("Starting Security Agents API...")
    logger.info("=" * 60)
    logger.info("Configuration Status:")
    logger.info("=" * 60)
    
    print("🚀 Starting up...")
    
    # Skip database initialization on startup for faster container startup
    # Database tables will be auto-created on first request via SQLModel
    # This prevents blocking the health endpoint during deployment
    logger.info("⚡ Fast startup mode - skipping DB initialization")
    logger.info("✅ Application ready to accept requests")
    logger.info("📝 Database tables will be created automatically on first use")
    
    yield
    
    print("🛑 Shutting down...")
 


"""Create and configure the FastAPI application"""
app = FastAPI(
    title="Security Agents API",
    version="2.0.0",
    description="Security Agents API with AWS Bedrock integration",
    openapi_url=f"{version_prefix}/openapi.json",
    docs_url=f"{version_prefix}/docs",
    redoc_url=f"{version_prefix}/redoc",
    lifespan=lifespan
)

# Register middleware (CORS, logging, trusted hosts)
register_middleware(app)

# Include routers with API v1 prefix
app.include_router(auth_router, prefix=f"{version_prefix}/auth", tags=["Auth"])
app.include_router(chat_router, prefix=f"{version_prefix}/chats", tags=["Chat"])
app.include_router(history_router, prefix=f"{version_prefix}/history", tags=["History"])
app.include_router(config_router, prefix=f"{version_prefix}/config", tags=["Config"])

# Health check endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint - always returns OK if app is running"""
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/api/v1/health", tags=["Health"])
async def api_health_check():
    """API health check endpoint with version info"""
    return {
        "status": "ok",
        "version": "2.0.0",
        "service": "security-agents-api",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

@app.get("/health/db", tags=["Health"])
async def database_health_check():
    """Database connectivity health check - initializes tables if needed"""
    try:
        # Initialize database tables if not already done
        await init_db()
        return {
            "status": "ok",
            "database": "connected",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "database": "disconnected",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        )


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint"""
    return {
        "message": "Security Agents API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health"
    }

if __name__ == "__main__":
    logger.info(f"Starting server on port 8000")
    
    # Use proper event loop for Windows psycopg compatibility
    if sys.platform == "win32":
        async def run_server():
            config = uvicorn.Config("main:app", host="127.0.0.1", port=8000, reload=True)
            server = uvicorn.Server(config)
            await server.serve()
        
        # Run with SelectorEventLoop as suggested by psycopg error
        asyncio.run(run_server(), loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))
    else:
        uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
