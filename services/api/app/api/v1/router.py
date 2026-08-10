"""API v1 router aggregator — combines all v1 endpoints."""

from fastapi import APIRouter

from app.api.v1 import auth, health, trees, upload

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(upload.router, prefix="/upload", tags=["upload"])
api_router.include_router(trees.router, prefix="/trees", tags=["trees"])
