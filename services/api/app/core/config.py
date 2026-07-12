"""Application settings loaded from environment variables.

Uses Pydantic Settings v2 for type-safe config with `.env` file support.
"""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- App ---
    APP_ENV: str = "development"
    APP_NAME: str = "CarbonScan AI API"
    APP_VERSION: str = "0.1.0"
    APP_DEBUG: bool = True
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_URL: str = "http://localhost:8000"

    # --- CORS (comma-separated list) ---
    CORS_ORIGINS: str = "http://localhost:3000"

    @property
    def CORS_ORIGINS_LIST(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    # --- Database ---
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/carbonscan",
    )
    DATABASE_ECHO: bool = False

    # --- Supabase ---
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    SUPABASE_STORAGE_BUCKET_POINTCLOUDS: str = "point-clouds"
    SUPABASE_STORAGE_BUCKET_PHOTOS: str = "photos"
    SUPABASE_STORAGE_BUCKET_REPORTS: str = "reports"

    # --- JWT ---
    JWT_SECRET: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # --- GPU Worker ---
    RUNPOD_API_KEY: str = ""
    RUNPOD_ENDPOINT_ID: str = ""

    # --- ML pipeline (sync MVP: shell out to the ml venv CLI) ---
    # Empty = auto-detect from the monorepo layout (services/ml + its .venv).
    ML_DIR: str = ""
    ML_PYTHON: str = ""

    # --- Queue ---
    # Jobs use the `jobs` table itself as the queue (claimed via
    # SELECT ... FOR UPDATE SKIP LOCKED in DbJobStore). No Redis/PGMQ needed.
    # See services/api/docs/WORKER_RUNBOOK.md.

    # --- File Upload ---
    MAX_UPLOAD_SIZE_MB: int = 500
    ALLOWED_LAS_EXTENSIONS: str = ".las,.laz,.ply"
    ALLOWED_IMAGE_EXTENSIONS: str = ".jpg,.jpeg,.png"

    # Where POST /jobs/analyze persists uploads for the worker to read.
    # Empty = <system temp>/carbonscan-jobs. Must be shared between API + worker.
    JOB_UPLOAD_DIR: str = ""

    @property
    def MAX_UPLOAD_SIZE_BYTES(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def ALLOWED_LAS_LIST(self) -> list[str]:
        return [e.strip().lower() for e in self.ALLOWED_LAS_EXTENSIONS.split(",")]

    @property
    def ALLOWED_IMAGE_LIST(self) -> list[str]:
        return [e.strip().lower() for e in self.ALLOWED_IMAGE_EXTENSIONS.split(",")]

    # --- Logging ---
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # --- Rate limiting ---
    RATE_LIMIT_AUTHENTICATED: int = 60
    RATE_LIMIT_PUBLIC: int = 20
    RATE_LIMIT_UPLOAD: int = 5


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()


# Module-level alias for convenience: `from app.core.config import settings`
settings = get_settings()
