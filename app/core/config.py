"""Application configuration"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Environment
    ENVIRONMENT: str = "development"
    
    # API
    API_KEY: str = "default-api-key"
    JWT_SECRET: str = "default-jwt-secret"
    
    # Database
    DATABASE_URL: str = "postgresql://synapse:synapse_password@localhost:5432/synapse_db"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # LLM Providers
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    MISTRAL_API_KEY: Optional[str] = None
    COHERE_API_KEY: Optional[str] = None
    REPLICATE_API_TOKEN: Optional[str] = None
    HUGGINGFACE_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None
    
    # Local models
    OLLAMA_HOST: Optional[str] = "http://localhost:11434"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Optional services
    SENTRY_DSN: Optional[str] = None
    ENABLE_PROMETHEUS: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()

# Validate critical settings
if settings.ENVIRONMENT == "production":
    if settings.API_KEY == "default-api-key":
        raise ValueError("API_KEY must be set in production")
    if settings.JWT_SECRET == "default-jwt-secret":
        raise ValueError("JWT_SECRET must be set in production")