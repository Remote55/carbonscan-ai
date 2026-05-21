"""FastAPI dependency-injection helpers."""

from collections.abc import AsyncGenerator
from typing import Annotated, Any

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import UnauthorizedError
from app.services.supabase import verify_supabase_token


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    """Verify the Bearer token (Supabase JWT) and return the user dict.

    Returns:
        Supabase user object (with .id, .email, .user_metadata, etc.)

    Raises:
        UnauthorizedError: if token missing, malformed, or invalid
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedError("Missing or malformed Authorization header")

    token = authorization.split(" ", 1)[1]
    user = await verify_supabase_token(token)
    if user is None:
        raise UnauthorizedError("Invalid or expired token")
    return user


async def get_current_user_id(
    user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> str:
    """Convenience: extract just the user ID."""
    return user["id"]


# Type aliases for ergonomics
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[dict[str, Any], Depends(get_current_user)]
CurrentUserId = Annotated[str, Depends(get_current_user_id)]


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Backward-compatible alias for `get_db`."""
    async for session in get_db():
        yield session
