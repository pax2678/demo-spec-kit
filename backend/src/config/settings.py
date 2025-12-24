from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, model_validator, Field
from typing import Optional, Union, List, Any
import os
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings and configuration."""
    
    # Application
    APP_NAME: str = "Dashboard API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # Database
    DATABASE_URL: str
    DB_ECHO: bool = False
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_PASSWORD: Optional[str] = None
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # File Upload
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    UPLOAD_DIR: str = "/tmp/uploads"
    
    # Export Settings
    EXPORT_CACHE_TTL: int = 3600  # 1 hour
    EXPORT_MAX_ROWS: int = 100000
    
    # Metrics Settings
    METRICS_RETENTION_DAYS: int = 90
    METRICS_AGGREGATION_INTERVAL: int = 300  # 5 minutes
    
    # Monitoring
    ENABLE_METRICS: bool = True
    METRICS_PATH: str = "/metrics"
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            # Handle comma-separated string from .env file
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, list):
            return v
        raise ValueError(f"Invalid CORS origins format: {v}")

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v):
        """Validate database URL format."""
        if not v.startswith(("postgresql://", "postgresql+psycopg2://")):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
        return v

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, v):
        """Parse DEBUG from string."""
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return v

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v):
        """Validate secret key strength."""
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        env_parse_none_str="None"
    )


class DevelopmentSettings(Settings):
    """Development environment settings."""
    DEBUG: bool = True
    DB_ECHO: bool = True
    LOG_LEVEL: str = "DEBUG"
    ENVIRONMENT: str = "development"


class ProductionSettings(Settings):
    """Production environment settings."""
    DEBUG: bool = False
    DB_ECHO: bool = False
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "production"
    LOG_FORMAT: str = "json"


class TestingSettings(Settings):
    """Testing environment settings."""
    DEBUG: bool = True
    ENVIRONMENT: str = "testing"
    DATABASE_URL: str = "sqlite:///./test.db"
    SECRET_KEY: str = "testing-secret-key-not-for-production"


@lru_cache()
def get_settings() -> Settings:
    """Get application settings based on environment."""
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    if environment == "development":
        return DevelopmentSettings()
    elif environment == "production":
        return ProductionSettings()
    elif environment == "testing":
        return TestingSettings()
    else:
        return Settings()


# Global settings instance
settings = get_settings()