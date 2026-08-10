"""FastAPI dependency-injection helpers.

There was a DbSession alias and a get_db_session generator here, over a
SQLAlchemy async engine. No table in that database had a reader or a writer,
so the whole layer has been removed — see docs/DATABASE_TEARDOWN.md.

What is left is the only dependency this service actually has: who is calling.
That is answered by Supabase over HTTP, not by a local table.
"""

from typing import Annotated, Any

from fastapi import Depends, Header

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


CurrentUser = Annotated[dict[str, Any], Depends(get_current_user)]
CurrentUserId = Annotated[str, Depends(get_current_user_id)]
