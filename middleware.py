from fastapi import FastAPI, status
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import time
import logging
from settings import settings

logger = logging.getLogger(__name__)


def register_middleware(app: FastAPI):
    """Register all middleware for the FastAPI application"""
    
    @app.middleware("http")
    async def custom_logging(request: Request, call_next):
        """Log all incoming requests with timing"""
        start_time = time.time()
        
        response = await call_next(request)
        processing_time = time.time() - start_time
        
        message = f"{request.client.host}:{request.client.port} - {request.method} - {request.url.path} - {response.status_code} completed after {processing_time:.3f}s"
        logger.info(message)
        
        return response
    
    # CORS Middleware
    allowed_origins = settings.allowed_origins_list
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
    
    # Trusted Host Middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=[
            "localhost",
            "da57vzl0vgd9l.cloudfront.net",
            "127.0.0.1",
            "0.0.0.0",
            "*",  
        ],
    )
    
    logger.info("✅ Middleware registered successfully")
