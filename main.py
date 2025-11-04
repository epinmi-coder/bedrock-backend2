# Main FastAPI application with clean lifecycle management
import sys
import asyncio

# Fix for Windows asyncio event loop compatibility with PostgreSQL
# MUST be set before any other imports that might use asyncio
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import os
import uvicorn
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from auth.routes import auth_router
from chats.routes import chat_router
from history.routes import history_router
from db.main import init_db
from middleware import register_middleware
from settings import settings
from logger import setup_logger

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
    await init_db()
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
)

# Register middleware (CORS, logging, trusted hosts)
register_middleware(app)

# Global exception handler
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "type": "internal_error",
            "path": str(request.url.path)
        }
    )

# Include routers with API v1 prefix
app.include_router(auth_router, prefix=f"{version_prefix}/auth", tags=["Auth"])
app.include_router(chat_router, prefix=f"{version_prefix}/chats", tags=["Chat"])
app.include_router(history_router, prefix=f"{version_prefix}/history", tags=["History"])

# Health check endpoints
@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint"""
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

    logger.info(f"Starting server on {settings.API_HOST}:{settings.API_PORT}")
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        log_level="info"
    )
