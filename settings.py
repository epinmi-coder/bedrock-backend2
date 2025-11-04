from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Optional
import os
import json


class Settings(BaseSettings):
    # Server Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = False
    
    # CORS 
    ALLOWED_ORIGINS: str = '["http://localhost:5173", "https://da57vzl0vgd9l.cloudfront.net"]'
    
    @property
    def allowed_origins_list(self) -> List[str]:
        """Parse ALLOWED_ORIGINS string to list"""
        try:
            return json.loads(self.ALLOWED_ORIGINS)
        except:
            return ["http://localhost:5173", "https://da57vzl0vgd9l.cloudfront.net"]

    # DATABASE 
    DATABASE_URL: str

    # AWS Configuration
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    
    # AWS BEDROCK 
    BEDROCK_MODEL_ID: str = "anthropic.claude-3-haiku-20240307-v1:0"
    BEDROCK_MAX_TOKENS: int = 4000
    BEDROCK_TEMPERATURE: float = 0.1

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"

    # Optional - Authentication (currently disabled)
    ENABLE_AUTH: bool = False
    JWT_SECRET: Optional[str] = None
    JWT_ALGORITHM: str = "HS256"
    
    # Optional - Redis
    REDIS_HOST: Optional[str] = None
    REDIS_PORT: int = 6379

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
