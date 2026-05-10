from __future__ import annotations

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.permissions import get_permissions_from_user
from app.core.security import decode_access_token
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    CurrentUserRead,
    LoginRequest,
    RefreshTokenRequest,
    TokenRead,
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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Extract the raw token from the Authorization header so we can blocklist its JTI.
    auth_header = request.headers.get("authorization", "")
    raw_token = auth_header[len("Bearer "):].strip() if auth_header.lower().startswith("bearer ") else ""
    token_payload = decode_access_token(raw_token) if raw_token else {}

    AuthService(db).logout(
        user=current_user,
        access_token_payload=token_payload,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )


@router.get("/me", response_model=CurrentUserRead, status_code=status.HTTP_200_OK)
def me(current_user: User = Depends(get_current_user)) -> CurrentUserRead:
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
    )


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    AuthService(db).change_password(user=current_user, payload=payload)