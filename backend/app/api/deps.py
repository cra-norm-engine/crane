from __future__ import annotations

from collections.abc import Callable
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.core.permissions import Permission

CurrentUser = dict[str, object]


def get_current_user(x_user_email: Annotated[str | None, Header(alias="X-User-Email")] = None) -> CurrentUser:
    if not x_user_email:
        return {
            "id": "00000000-0000-0000-0000-000000000000",
            "email": "admin@example.com",
            "roles": ["admin"],
        }

    return {
        "id": "00000000-0000-0000-0000-000000000000",
        "email": x_user_email,
        "roles": ["admin"],
    }


def require_permission(permission: Permission) -> Callable[..., CurrentUser]:
    def dependency(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        roles = user.get("roles", [])
        if "admin" in roles:
            return user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Missing permission: {permission.value}",
        )

    return dependency
