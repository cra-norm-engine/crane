from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=255)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenRead(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class CurrentUserRead(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    roles: list[str]
    permissions: list[str]
    is_active: bool
    auth_provider: str
    must_change_password: bool


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=255)
    new_password: str = Field(min_length=8, max_length=255)


class AdminPasswordResetRequest(BaseModel):
    """Admin sets a new temporary password for a local user."""
    new_password: str = Field(min_length=8, max_length=255)