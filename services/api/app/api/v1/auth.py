"""Authentication endpoints — stub for Phase 1.

TODO Phase 1:
- Implement signup/login with Supabase Auth or local
- Refresh token rotation
- Email verification
- Password reset
"""

from fastapi import APIRouter

router = APIRouter()


@router.post("/signup", status_code=501)
async def signup() -> dict[str, str]:
    """Sign up a new user. TODO: implement."""
    return {"message": "Not implemented — see TODO in auth.py"}


@router.post("/login", status_code=501)
async def login() -> dict[str, str]:
    """Login and receive JWT tokens. TODO: implement."""
    return {"message": "Not implemented — see TODO in auth.py"}


@router.post("/refresh", status_code=501)
async def refresh() -> dict[str, str]:
    """Refresh access token using refresh token. TODO: implement."""
    return {"message": "Not implemented — see TODO in auth.py"}


@router.post("/logout", status_code=501)
async def logout() -> dict[str, str]:
    """Logout (invalidate refresh token). TODO: implement."""
    return {"message": "Not implemented — see TODO in auth.py"}
