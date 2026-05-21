"""FastAPI dependency-injection helpers."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import UnauthorizedError
from app.core.security import JWTError, decode_token


async def get_current_user_id(
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    """Extract user ID from JWT in Authorization header.

    Returns:
        str: User UUID

    Raises:
        UnauthorizedError: if token missing or invalid
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedError("Missing or malformed Authorization header")

    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_token(token)
    except JWTError as exc:
        raise UnauthorizedError("Invalid or expired token") from exc

    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedError("Token missing subject claim")

    return user_id


# Type aliases for ergonomics
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUserId = Annotated[str, Depends(get_current_user_id)]


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Backward-compatible alias for `get_db`."""
    async for session in get_db():
        yield session
