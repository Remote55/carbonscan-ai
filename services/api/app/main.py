"""FastAPI application entry point.

Run locally:
    uvicorn app.main:app --reload

Production:
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
"""

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.demo_security import DemoGuardMiddleware
from app.core.exceptions import AppException
from app.core.logging import RequestContextMiddleware, configure_logging, current_request_id

configure_logging()
logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Application lifespan — startup and shutdown hooks."""
    logger.info(
        "startup",
        version=__version__,
        environment=settings.APP_ENV,
        debug=settings.APP_DEBUG,
        max_concurrent_analyses=settings.MAX_CONCURRENT_ANALYSES,
        trust_proxy_headers=settings.TRUST_PROXY_HEADERS,
    )
    yield
    logger.info("shutdown")


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
# Added last, so it runs first: the guard below can reject a request before any
# route sees it, and that rejection still needs a request id on its log line.
app.add_middleware(DemoGuardMiddleware)
app.add_middleware(RequestContextMiddleware)

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


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Anything not an AppException.

    Without this the traceback went to whatever uvicorn's logger was doing and
    the caller got a bare 500 with nothing to quote. The message is deliberately
    generic — an exception string can carry a filesystem path or a query — and
    the request id is the thread back to the logged traceback.
    """
    request_id = current_request_id(request.scope)
    logger.exception(
        "unhandled_exception",
        request_id=request_id,
        path=request.url.path,
        method=request.method,
        exc_type=type(exc).__name__,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "The request could not be completed.",
            "request_id": request_id,
        },
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
