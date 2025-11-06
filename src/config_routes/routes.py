"""
Frontend Configuration Endpoint
Provides frontend-safe configuration without exposing secrets
"""
from fastapi import APIRouter
from src.config import Config as settings

config_router = APIRouter()


@config_router.get("/frontend")
async def get_frontend_config():
    """
    Return frontend-safe configuration
    DO NOT expose secrets like JWT_SECRET, AWS keys, or database credentials
    
    Returns:
        dict: Frontend-safe configuration including:
            - api_base_url: Base URL for API requests
            - app_name: Application name
            - app_version: Application version
            - require_auth: Whether authentication is required
            - enable_auth: Whether authentication is enabled
            - features: Available features
    """
    # Construct base URL from domain
    protocol = "https" if settings.DOMAIN and not settings.DOMAIN.startswith("localhost") else "http"
    base_url = f"{protocol}://{settings.DOMAIN}" if settings.DOMAIN else "http://localhost:8000"
    
    return {
        "api_base_url": base_url,
        "app_name": "Security Assistant",
        "app_version": "2.0.0",
        "require_auth": False,  # Set to True when auth is enforced
        "enable_auth": True,    # Auth endpoints are available
        "features": {
            "email_verification": True,
            "password_reset": True,
            "chat_history": True,
            "bedrock_ai": True,
            "anonymous_chat": True
        },
        "limits": {
            "max_message_length": 4000,
            "cache_duration_seconds": 30
        }
    }
