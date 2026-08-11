"""Supabase service helpers.

Provides:
- Async client for verifying Supabase JWTs (via /auth/v1/user)
- Admin client using service_role key (for backend-side ops that bypass RLS)
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

import httpx

from app.core.config import settings


@lru_cache
def get_supabase_admin_headers() -> dict[str, str]:
    """Headers for admin-level Supabase REST calls (service_role)."""
    return {
        "apikey": settings.SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_SERVICE_KEY}",
    }


async def verify_supabase_token(jwt_token: str) -> dict[str, Any] | None:
    """Verify a Supabase JWT by calling GET /auth/v1/user.

    This is the recommended path for backend verification — Supabase validates
    the token signature on their side and returns the user object.

    Args:
        jwt_token: The JWT extracted from the Authorization header

    Returns:
        User dict from Supabase if valid, None if invalid/expired.
    """
    if not settings.SUPABASE_URL:
        return None

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.get(
                f"{settings.SUPABASE_URL}/auth/v1/user",
                headers={
                    "Authorization": f"Bearer {jwt_token}",
                    "apikey": settings.SUPABASE_ANON_KEY,
                },
            )
        except httpx.HTTPError:
            return None

    if response.status_code != 200:
        return None

    user: dict[str, Any] = response.json()
    return user


# sync_user_to_db was here: a function whose body was `return None`, with a
# docstring describing an upsert it did not perform and a comment pointing at
# DbJobStore.create, which was deleted with the async queue. Nothing called it.
# A no-op that documents behaviour it does not have is worse than nothing,
# because it reads like the feature exists.
#
# If a /me sync is wanted later, the public.users table it would write to has
# no reader either — see the note in alembic/versions/0004_drop_trees.py.
