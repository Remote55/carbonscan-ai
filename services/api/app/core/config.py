"""Application settings loaded from environment variables.

Uses Pydantic Settings v2 for type-safe config with `.env` file support.
"""

from functools import lru_cache

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
    # APP_VERSION sat here as a second version string. app.__version__ is the one
    # /health and the OpenAPI document report, and two of them can disagree.
    # APP_URL, APP_HOST and APP_PORT were also unread: uvicorn is told where to
    # bind on its command line, in the Dockerfile CMD.
    APP_DEBUG: bool = True

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

    # DATABASE_URL and DATABASE_ECHO sat here, over a SQLAlchemy async engine,
    # alembic and six tables. Not one of those tables had a reader or a writer:
    # jobs went with the async queue, trees could not be filled because nothing
    # produces a WGS84 coordinate, and users, plots, transactions and species_db
    # were never touched by any code path. This service stores nothing between
    # requests — an analysis is computed and returned. See
    # docs/DATABASE_TEARDOWN.md for the tables left standing in Supabase and the
    # SQL to remove them.

    # --- Supabase ---
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_KEY: str = ""
    # Three SUPABASE_STORAGE_BUCKET_* names were here. None was read: PHOTOS was
    # for a photo path that has been dropped, REPORTS for a report generator
    # that does not exist, and POINTCLOUDS for an upload route that writes to a
    # temp file for the length of one request and deletes it. Nothing in this
    # service touches Supabase Storage — see the TODO in api/v1/upload.py, which
    # is where a bucket name would start being needed.

    # There was a JWT block here — JWT_SECRET defaulting to the literal string
    # "change-me", plus an algorithm and two expiry windows — feeding
    # app/core/security.py, which implemented bcrypt password hashing and a
    # full token issue/verify pair. Nothing in the application or its tests
    # imported any of it: authentication is Supabase's, verified in
    # app/services/supabase.py and wired in app/api/deps.py.
    #
    # Deleted rather than left dormant. A signing key that ships with a public
    # default is only harmless while nobody calls the function that uses it,
    # and the next person to add `Depends(decode_token)` would have inherited
    # it silently. It also carried python-jose and passlib into the image.

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

    @property
    def MAX_UPLOAD_SIZE_BYTES(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    # ALLOWED_LAS_EXTENSIONS / ALLOWED_IMAGE_EXTENSIONS and their list
    # properties were here and nothing read them. The accepted set is
    # upload_validation.ANALYZE_EXTENSIONS, which is what the pipeline can
    # load. Worse than dead: ALLOWED_LAS_EXTENSIONS said ".las,.laz,.ply",
    # narrower than what the route actually accepts, so anyone reading config
    # to find out got the wrong answer. The image list described a photo path
    # that no longer exists.

    # --- Logging ---
    #: Read by app/core/logging.py at startup. These were declared and unread
    #: for long enough that LOG_FORMAT="json" promised structured logs the
    #: service did not emit — it printed with print().
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
