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

    # --- Ephemeral judge demo ---
    TREEQ_DEMO_MODE: bool = False
    TREEQ_DEMO_TOKEN: str = ""
    TREEQ_DEMO_MAX_UPLOAD_SIZE_MB: int = 100
    TREEQ_DEMO_MAX_POINTS: int = 2_000_000
    TREEQ_DEMO_ALLOWED_ORIGINS: str = (
        "https://treeqcarbon.vercel.app,http://127.0.0.1:3000,http://localhost:3000"
    )

    @property
    def CORS_ORIGINS_LIST(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def TREEQ_DEMO_MAX_UPLOAD_SIZE_BYTES(self) -> int:
        return self.TREEQ_DEMO_MAX_UPLOAD_SIZE_MB * 1024 * 1024

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

    # RUNPOD_API_KEY and RUNPOD_ENDPOINT_ID used to sit here. Nothing read them:
    # the production wood/leaf backend is tlsep, which is numpy and a KD-tree,
    # and the deployed image carries no torch. Settings that name an
    # architecture the code does not have send the next reader looking for a GPU
    # path that was never built.

    # --- ML pipeline (sync MVP: shell out to the ml venv CLI) ---
    # Empty = auto-detect from the monorepo layout (services/ml + its .venv).
    ML_DIR: str = ""
    ML_PYTHON: str = ""

    # There was an async job queue here — a `jobs` table claimed with
    # SELECT ... FOR UPDATE SKIP LOCKED, a worker process, and JOB_UPLOAD_DIR
    # for handing uploads between them. Nothing in the web app ever called it,
    # no deployment ever started the worker, and POST /jobs/analyze answered 202
    # "queued" for work that could not run. Analysis is synchronous: the pipeline
    # measured a 16-tree plot of 447,089 points in 10 seconds and this service
    # caps an analysis at 200,000, so a request finishes well inside a request.

    # --- File Upload ---
    MAX_UPLOAD_SIZE_MB: int = 500
    ALLOWED_LAS_EXTENSIONS: str = ".las,.laz,.ply"
    ALLOWED_IMAGE_EXTENSIONS: str = ".jpg,.jpeg,.png"

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
    # RATE_LIMIT_AUTHENTICATED and RATE_LIMIT_PUBLIC used to sit here. Nothing
    # read either one, so they described a tiering this service does not have.
    RATE_LIMIT_UPLOAD: int = 5

    #: Analyses allowed to run at once in this process, across all callers.
    #: The rate limit bounds how often ONE client may ask; this bounds how much
    #: work is in flight, which is what decides whether the host survives.
    #: See app/services/analysis_slots.py.
    MAX_CONCURRENT_ANALYSES: int = 2

    #: Trust X-Forwarded-For for the client address used by the rate limiter.
    #: Off by default: with no proxy in front, that header is caller-controlled,
    #: and honouring it would let anyone mint a fresh identity per request and
    #: erase the limit. Turn it ON behind Railway / Fly / HF Spaces / Cloudflare,
    #: where the socket peer is the proxy and every caller otherwise shares one
    #: bucket — which throttles the whole world to RATE_LIMIT_UPLOAD together.
    TRUST_PROXY_HEADERS: bool = False


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()


# Module-level alias for convenience: `from app.core.config import settings`
settings = get_settings()
