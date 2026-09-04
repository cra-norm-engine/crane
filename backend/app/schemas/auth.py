# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.password_policy import StrongPassword


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=255)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    # Optional: when supplied, the refresh token is also revoked on logout so it
    # can no longer mint access tokens (M-04). Logout still succeeds without it.
    refresh_token: str | None = None


class TokenRead(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserPreferenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    theme: str
    timezone: str
    date_format: str
    default_landing_page: str


class UserPreferenceUpdate(BaseModel):
    """Partial update of personal preferences; only provided fields change."""

    theme: str | None = Field(default=None, max_length=20)
    timezone: str | None = Field(default=None, max_length=64)
    date_format: str | None = Field(default=None, max_length=32)
    default_landing_page: str | None = Field(default=None, max_length=64)


class ProfileUpdateRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)


class CurrentUserRead(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    avatar_data: str | None = None
    roles: list[str]
    permissions: list[str]
    is_active: bool
    auth_provider: str
    must_change_password: bool
    preferences: UserPreferenceRead


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=255)
    new_password: StrongPassword


class AdminPasswordResetRequest(BaseModel):
    """Admin sets a new temporary password for a local user."""
    new_password: StrongPassword
