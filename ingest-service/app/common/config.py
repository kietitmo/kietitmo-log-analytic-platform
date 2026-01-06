"""
Configuration management for the ingest service.
Uses Pydantic Settings for validation and type safety.
"""
import os
from typing import Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    APP_NAME: str = Field(default="Log Ingest Service", description="Application name")
    APP_VERSION: str = Field(default="1.0.0", description="Application version")
    DEBUG: bool = Field(default=False, description="Debug mode")
    ENVIRONMENT: str = Field(default="development", description="Environment (development/staging/production)")
    
    # Server
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql://postgres:postgres@ingest-postgres:5432/logs",
        description="PostgreSQL database URL"
    )
    DB_POOL_SIZE: int = Field(default=10, description="Database connection pool size")
    DB_MAX_OVERFLOW: int = Field(default=20, description="Database max overflow connections")
    DB_POOL_TIMEOUT: int = Field(default=30, description="Database pool timeout in seconds")
    DB_POOL_RECYCLE: int = Field(default=3600, description="Database connection recycle time in seconds")
    
    # Redis
    REDIS_URL: str = Field(
        default="redis://ingest-redis:6379",
        description="Redis connection URL"
    )
    REDIS_STREAM_KEY: str = Field(
        default="log_jobs",
        description="Redis stream key for job queue"
    )
    REDIS_SOCKET_TIMEOUT: int = Field(default=5, description="Redis socket timeout in seconds")
    REDIS_SOCKET_CONNECT_TIMEOUT: int = Field(default=5, description="Redis connection timeout in seconds")
    
    # S3/MinIO
    S3_ENDPOINT: str = Field(
        default="http://ingest-minio:9000",
        description="S3 endpoint URL"
    )
    S3_ACCESS_KEY: str = Field(
        default="minioadmin",
        description="S3 access key"
    )
    S3_SECRET_KEY: str = Field(
        default="minioadmin",
        description="S3 secret key"
    )
    S3_BUCKET: str = Field(
        default="log-bucket",
        description="S3 bucket name"
    )
    S3_REGION: str = Field(
        default="us-east-1",
        description="S3 region"
    )
    S3_PRESIGNED_URL_EXPIRES: int = Field(
        default=1800,
        description="Presigned URL expiration time in seconds"
    )
    
    # Job Configuration
    MAX_RETRY_COUNT: int = Field(default=3, description="Maximum job retry count")
    JOB_TIMEOUT_SECONDS: int = Field(default=3600, description="Job timeout in seconds")
    
    # CORS
    CORS_ORIGINS: list[str] = Field(
        default=["*"],
        description="Allowed CORS origins"
    )
    CORS_CREDENTIALS: bool = Field(default=True, description="Allow CORS credentials")
    CORS_METHODS: list[str] = Field(
        default=["*"],
        description="Allowed CORS methods"
    )
    CORS_HEADERS: list[str] = Field(
        default=["*"],
        description="Allowed CORS headers"
    )
    
    # JWT Authentication
    JWT_SECRET_KEY: str = Field(
        default="your-secret-key-change-in-production",
        description="JWT secret key for token signing (MUST be set in production)"
    )
    JWT_ALGORITHM: str = Field(
        default="HS256",
        description="JWT algorithm"
    )
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        description="JWT access token expiration time in minutes"
    )
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        description="JWT refresh token expiration time in days"
    )
    JWT_TOKEN_PREFIX: str = Field(
        default="Bearer",
        description="JWT token prefix in Authorization header"
    )
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(
        default=True,
        description="Enable rate limiting"
    )
    RATE_LIMIT_PER_MINUTE: int = Field(
        default=60,
        description="Rate limit per minute per IP"
    )
    RATE_LIMIT_PER_HOUR: int = Field(
        default=1000,
        description="Rate limit per hour per IP"
    )
    RATE_LIMIT_STORAGE_URI: Optional[str] = Field(
        default=None,
        description="Redis URI for rate limit storage (uses REDIS_URL if not set)"
    )
    
    # Request Timeout
    REQUEST_TIMEOUT_SECONDS: int = Field(
        default=30,
        description="Request timeout in seconds"
    )
    REQUEST_TIMEOUT_ENABLED: bool = Field(
        default=True,
        description="Enable request timeout"
    )
    
    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, v: str, info) -> str:
        """Validate database URL format."""
        env = info.data.get("ENVIRONMENT")

        if env == "test":
            return v
        
        if not v.startswith(("postgresql://", "postgresql+psycopg2://")):
            raise ValueError("DATABASE_URL must be a PostgreSQL connection string")
        return v
    
    @field_validator("REDIS_URL")
    @classmethod
    def validate_redis_url(cls, v: str) -> str:
        """Validate Redis URL format."""
        if not v.startswith(("redis://", "rediss://")):
            raise ValueError("REDIS_URL must be a Redis connection string")
        return v
    
    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment value."""
        allowed = {"development", "staging", "production", "test"}
        if v.lower() not in allowed:
            raise ValueError(f"ENVIRONMENT must be one of {allowed}")
        return v.lower()
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.ENVIRONMENT == "development"
    
    def validate_production(self) -> None:
        """Validate production configuration."""
        if not self.is_production:
            return
        
        errors = []
        
        # Check JWT secret key
        if self.JWT_SECRET_KEY == "your-secret-key-change-in-production":
            errors.append("JWT_SECRET_KEY must be set to a secure value in production")
        
        # Check CORS origins
        if "*" in self.CORS_ORIGINS:
            errors.append("CORS_ORIGINS cannot contain '*' in production")
        
        # Check S3 credentials
        if self.S3_ACCESS_KEY == "minioadmin" or self.S3_SECRET_KEY == "minioadmin":
            errors.append("S3 credentials must not use default values in production")
        
        # Check debug mode
        if self.DEBUG:
            errors.append("DEBUG must be False in production")
        
        if errors:
            raise ValueError(f"Production configuration errors: {'; '.join(errors)}")


# Global settings instance
settings = Settings()

