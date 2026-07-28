"""FastAPI application entry point.

Run locally:
    uvicorn app.main:app --reload

Production:
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.demo_security import DemoGuardMiddleware
from app.core.exceptions import AppException


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application lifespan — startup and shutdown hooks."""
    # Startup
    print(f"Starting CarbonScan AI API v{__version__} ({settings.APP_ENV})")
    # TODO: warm up DB connection pool, ML model cache, etc.
    yield
    # Shutdown
    print("Shutting down CarbonScan AI API")
    # TODO: close DB connections, flush logs, etc.


app = FastAPI(
    title=settings.APP_NAME,
    version=__version__,
    description="Backend API for CarbonScan AI — Tree Biomass Carbon Assessment Platform",
    docs_url="/docs" if settings.APP_DEBUG else None,
    redoc_url="/redoc" if settings.APP_DEBUG else None,
    openapi_url="/openapi.json" if settings.APP_DEBUG else None,
    lifespan=lifespan,
)

# --- Middleware ---
app.add_middleware(DemoGuardMiddleware)

cors_origins = settings.CORS_ORIGINS_LIST
if settings.TREEQ_DEMO_MODE:
    demo_origins = [
        origin.strip()
        for origin in settings.TREEQ_DEMO_ALLOWED_ORIGINS.split(",")
        if origin.strip()
    ]
    cors_origins = list(dict.fromkeys([*cors_origins, *demo_origins]))

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Exception handlers ---
@app.exception_handler(AppException)
async def app_exception_handler(_request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error_code, "message": exc.message, "details": exc.details},
    )


# --- Routes ---
@app.get("/", tags=["root"])
async def root():
    """Root endpoint — API information."""
    return {
        "name": settings.APP_NAME,
        "version": __version__,
        "environment": settings.APP_ENV,
        "docs": "/docs" if settings.APP_DEBUG else "disabled",
    }


@app.get("/health", tags=["root"])
async def health():
    """Liveness probe."""
    return {"status": "ok", "version": __version__}


app.include_router(api_router, prefix="/api/v1")
