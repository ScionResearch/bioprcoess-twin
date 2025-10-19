"""
Application configuration using Pydantic Settings.
Loads configuration from environment variables.
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "pichia_manual_data"
    POSTGRES_USER: str = "pichia_api"
    POSTGRES_PASSWORD: str

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Pichia pastoris Digital Twin API"
    DEBUG: bool = False

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100

    @property
    def DATABASE_URL(self) -> str:
        """Construct async PostgreSQL URL."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def DATABASE_URL_SYNC(self) -> str:
        """Construct sync PostgreSQL URL (for Alembic)."""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def ALLOWED_ORIGINS_LIST(self) -> List[str]:
        """Convert comma-separated CORS origins to list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
