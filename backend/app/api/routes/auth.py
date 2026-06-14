# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_current_user_password_change_exempt
from app.core.database import get_db
from app.core.permissions import get_permissions_from_user
from app.core.security import decode_access_token
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    CurrentUserRead,
    LoginRequest,
    LogoutRequest,
    ProfileUpdateRequest,
    RefreshTokenRequest,
    TokenRead,
    UserPreferenceRead,
    UserPreferenceUpdate,
)
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/login", response_model=TokenRead, status_code=status.HTTP_200_OK)
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenRead:
    return AuthService(db).login(
        payload=payload,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


@router.post("/refresh", response_model=TokenRead, status_code=status.HTTP_200_OK)
def refresh(
    payload: RefreshTokenRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> TokenRead:
    return AuthService(db).refresh(
        refresh_token=payload.refresh_token,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    request: Request,
    body: LogoutRequest | None = None,
    current_user: User = Depends(get_current_user_password_change_exempt),
    db: Session = Depends(get_db),
):
    # Extract the raw token from the Authorization header so we can blocklist its JTI.
    auth_header = request.headers.get("authorization", "")
    raw_token = auth_header[len("Bearer "):].strip() if auth_header.lower().startswith("bearer ") else ""
    token_payload = decode_access_token(raw_token) if raw_token else {}

    AuthService(db).logout(
        user=current_user,
        access_token_payload=token_payload,
        refresh_token=body.refresh_token if body else None,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


@router.get("/me", response_model=CurrentUserRead, status_code=status.HTTP_200_OK)
def me(
    current_user: User = Depends(get_current_user_password_change_exempt),
    db: Session = Depends(get_db),
) -> CurrentUserRead:
    permissions = sorted(permission.value for permission in get_permissions_from_user(current_user))

    return CurrentUserRead(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        roles=current_user.role_names,
        permissions=permissions,
        is_active=current_user.is_active,
        auth_provider=current_user.auth_provider,
        must_change_password=current_user.must_change_password,
        preferences=AuthService(db).read_preferences(user=current_user),
    )


@router.patch("/me/profile", response_model=CurrentUserRead, status_code=status.HTTP_200_OK)
def update_profile(
    payload: ProfileUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CurrentUserRead:
    service = AuthService(db)
    updated = service.update_profile(user=current_user, payload=payload)
    permissions = sorted(permission.value for permission in get_permissions_from_user(updated))
    return CurrentUserRead(
        id=str(updated.id),
        email=updated.email,
        full_name=updated.full_name,
        roles=updated.role_names,
        permissions=permissions,
        is_active=updated.is_active,
        auth_provider=updated.auth_provider,
        must_change_password=updated.must_change_password,
        preferences=service.read_preferences(user=updated),
    )


@router.get("/me/preferences", response_model=UserPreferenceRead, status_code=status.HTTP_200_OK)
def get_preferences(
    current_user: User = Depends(get_current_user_password_change_exempt),
    db: Session = Depends(get_db),
) -> UserPreferenceRead:
    return AuthService(db).read_preferences(user=current_user)


@router.put("/me/preferences", response_model=UserPreferenceRead, status_code=status.HTTP_200_OK)
def update_preferences(
    payload: UserPreferenceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserPreferenceRead:
    return AuthService(db).update_preferences(user=current_user, payload=payload)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
def logout_all(
    request: Request,
    current_user: User = Depends(get_current_user_password_change_exempt),
    db: Session = Depends(get_db),
):
    AuthService(db).logout_all_sessions(
        user=current_user,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user_password_change_exempt),
    db: Session = Depends(get_db),
):
    AuthService(db).change_password(user=current_user, payload=payload)