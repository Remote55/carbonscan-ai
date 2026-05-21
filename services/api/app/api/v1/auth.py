"""Authentication endpoints.

Auth flow (Pattern B — recommended by Supabase):
1. Web client uses Supabase JS SDK directly for signup/login (apps/web/src/lib/auth.ts)
2. Supabase issues JWT and stores in HttpOnly cookie
3. Web sends `Authorization: Bearer <jwt>` to FastAPI
4. FastAPI verifies via GET /auth/v1/user (services/supabase.verify_supabase_token)
5. /me endpoint returns user info

Backend does NOT handle email/password directly — Supabase Auth manages it
including email verification, password reset, OAuth, etc.

TODO Phase 1:
- Add user sync trigger (insert into public.users on first /me call)
- Add /logout endpoint (optional — client can clear session locally)
- Add OAuth provider callbacks
"""

from fastapi import APIRouter

from app.api.deps import CurrentUser
from app.schemas.auth import UserMetadata, UserOut

router = APIRouter()


@router.get("/me", response_model=UserOut)
async def get_me(user: CurrentUser) -> UserOut:
    """Return the current authenticated user's profile.

    Requires `Authorization: Bearer <supabase-jwt>` header.
    """
    metadata = UserMetadata(**user.get("user_metadata", {}))
    return UserOut(
        id=user["id"],
        email=user["email"],
        name=metadata.name,
        role=metadata.role,
        created_at=user.get("created_at"),
    )


@router.post("/signup", status_code=501)
async def signup() -> dict[str, str]:
    """⚠ Backend does NOT handle signup directly.

    Web app uses Supabase JS SDK on client-side. This endpoint exists only
    to document that and return a helpful error.

    See: apps/web/src/lib/auth.ts → signUp()
    """
    return {
        "error": "NotImplemented",
        "message": "Backend doesn't handle signup. Use Supabase JS SDK from Web client.",
        "hint": "POST to https://<project>.supabase.co/auth/v1/signup directly",
    }


@router.post("/login", status_code=501)
async def login() -> dict[str, str]:
    """⚠ Backend does NOT handle login directly.

    Same as /signup — Web uses Supabase JS SDK.
    """
    return {
        "error": "NotImplemented",
        "message": "Backend doesn't handle login. Use Supabase JS SDK from Web client.",
        "hint": "supabase.auth.signInWithPassword(...) in apps/web/src/lib/auth.ts",
    }
