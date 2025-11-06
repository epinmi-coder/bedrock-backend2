from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pydantic import field_validator


class Settings(BaseSettings):
    DATABASE_URL: str
    
    # JWT Configuration - Optional when ENABLE_AUTH is False
    JWT_SECRET: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"
    ENABLE_AUTH: bool = True  # Set to False to disable authentication requirement
    
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: str = "redis://localhost:6379/0"
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_FROM_NAME: str
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = True
    DOMAIN: str
    FRONTEND_DOMAIN: str = "localhost:5173"  # Default frontend domain
    # AWS Configuration
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    
    # AWS BEDROCK 
    BEDROCK_MODEL_ID: str = "anthropic.claude-3-haiku-20240307-v1:0"
    BEDROCK_MAX_TOKENS: int = 4000
    BEDROCK_TEMPERATURE: float = 0.1

    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    
    # CORS Configuration
    ALLOWED_ORIGINS: str = '["http://localhost:5173", "http://localhost:5174"]'
    
    @field_validator('JWT_SECRET')
    @classmethod
    def validate_jwt_secret(cls, v, info):
        """Require JWT_SECRET if ENABLE_AUTH is True"""
        # Get ENABLE_AUTH from validation context
        enable_auth = info.data.get('ENABLE_AUTH', True)
        if enable_auth and not v:
            raise ValueError('JWT_SECRET is required when ENABLE_AUTH=True')
        return v
    
    @field_validator('ALLOWED_ORIGINS')
    @classmethod
    def parse_origins(cls, v):
        """Parse ALLOWED_ORIGINS string to list"""
        import json
        try:
            origins = json.loads(v)
            if not isinstance(origins, list):
                raise ValueError("ALLOWED_ORIGINS must be a JSON array")
            return origins
        except json.JSONDecodeError as e:
            # Fallback to default on parse error
            return ["http://localhost:5173", "http://localhost:5174"]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


Config = Settings()


broker_url = Config.REDIS_URL
result_backend = Config.REDIS_URL
broker_connection_retry_on_startup = True
