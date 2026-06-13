# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import AppException
from app.core.permissions import Permission, require_permissions
from app.core.security import decode_access_token, get_token_subject
from app.models.revoked_token import RevokedToken
from app.models.user import User
from app.repositories.user_repository import UserRepository

security_scheme = HTTPBearer(auto_error=False)


def _resolve_authenticated_user(
    credentials: HTTPAuthorizationCredentials | None,
    db: Session,
) -> User:
    """Validate the bearer token and return the active user it identifies.

    Does NOT enforce ``must_change_password`` — that gate lives in
    ``get_current_user`` so the password-change flow can use the exempt variant.
    """
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    subject = get_token_subject(payload)

    # Reject tokens that were explicitly revoked (e.g. via logout).
    jti = payload.get("jti")
    if jti and db.get(RevokedToken, jti) is not None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = UUID(subject)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token subject",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = UserRepository(db).get_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Reject tokens minted before the user's token_version was last bumped
    # (e.g. after a password change). Missing claim is treated as version 0 so
    # tokens issued before this feature remain valid until they expire (M-04).
    if payload.get("ver", 0) != user.token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been invalidated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)],
    db: Session = Depends(get_db),
) -> User:
    """Default auth dependency: also enforces a pending password change (M-03).

    While ``must_change_password`` is set, every protected endpoint is blocked with
    403 ``PASSWORD_CHANGE_REQUIRED``. The only endpoints that should remain usable
    (``/auth/me``, ``/auth/change-password``, ``/auth/logout``) depend on
    ``get_current_user_password_change_exempt`` instead.
    """
    user = _resolve_authenticated_user(credentials, db)
    if user.must_change_password:
        raise AppException(
            "Password change required before accessing this resource.",
            status_code=status.HTTP_403_FORBIDDEN,
            code="PASSWORD_CHANGE_REQUIRED",
        )
    return user


def get_current_user_password_change_exempt(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security_scheme)],
    db: Session = Depends(get_db),
) -> User:
    """Auth dependency that does NOT enforce ``must_change_password``.

    Used only by the endpoints a user must reach in order to resolve a forced
    password change (view self, change password, log out).
    """
    return _resolve_authenticated_user(credentials, db)


def require_permission(permission: Permission):
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        require_permissions(current_user, {permission})
        return current_user

    return dependency


def require_permissions_dependency(*permissions: Permission):
    required = set(permissions)

    def dependency(current_user: User = Depends(get_current_user)) -> User:
        require_permissions(current_user, required)
        return current_user

    return dependency


CurrentUser = Annotated[User, Depends(get_current_user)]