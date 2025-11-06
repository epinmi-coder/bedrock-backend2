from fastapi import FastAPI, status
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
import time
import logging
from src.config import Config as settings

logger = logging.getLogger(__name__)


def register_middleware(app: FastAPI):
    """Register all middleware for the FastAPI application"""
    
    @app.middleware("http")
    async def add_request_id_and_logging(request: Request, call_next):
        """Add unique request ID and log all incoming requests with timing"""
        import uuid
        
        # Generate unique request ID for tracking
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        start_time = time.time()
        
        response = await call_next(request)
        processing_time = time.time() - start_time
        
        # Add request ID to response headers for debugging
        response.headers["X-Request-ID"] = request_id
        
        message = f"[{request_id}] {request.client.host}:{request.client.port} - {request.method} - {request.url.path} - {response.status_code} completed after {processing_time:.3f}s"
        logger.info(message)
        
        return response
    
    # CORS Middleware
    # ALLOWED_ORIGINS is already parsed to list by field_validator
    allowed_origins = settings.ALLOWED_ORIGINS
    logger.info(f"CORS allowed origins: {allowed_origins}")
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        allow_credentials=True,
    )
    logger.info("✅ CORS middleware configured successfully")
    
    # Trusted Host Middleware - Allow all hosts for AWS ALB compatibility
    # In production with ALB, requests come with ALB DNS as Host header
    # We rely on ALB security groups and CORS for access control
    allowed_hosts = ["*"]
    
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=allowed_hosts
    )
    logger.info(f"✅ Trusted host middleware configured: {allowed_hosts}")
    
    logger.info("✅ Middleware registered successfully")
