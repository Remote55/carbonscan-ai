"""Pydantic schemas for authentication endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

UserRole = Literal["community", "industrial", "auditor", "admin"]


class UserOut(BaseModel):
    """Public user info returned from /me and similar endpoints."""

    id: str
    email: EmailStr
    name: str | None = None
    role: UserRole = "community"
    organization: str | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class UserMetadata(BaseModel):
    """User metadata stored in Supabase auth.users.raw_user_meta_data."""

    name: str | None = None
    role: UserRole = "community"


class SupabaseUserResponse(BaseModel):
    """Shape of Supabase's GET /auth/v1/user response (partial)."""

    id: str
    email: EmailStr
    user_metadata: UserMetadata = Field(default_factory=UserMetadata)
    created_at: datetime
