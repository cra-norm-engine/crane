from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_permissions_dependency
from app.core.database import get_db
from app.core.permissions import Permission
from app.models.user import User
from app.schemas.admin_user import (
    AdminUserCreate,
    AdminUserRead,
    AdminUserRoleUpdate,
    AdminUserStatusUpdate,
)
from app.schemas.auth import AdminPasswordResetRequest
from app.schemas.permission import PermissionRead
from app.schemas.role import RoleCreate, RolePermissionsUpdate, RoleRead, RoleUpdate
from app.services.admin_user_service import AdminUserService
from app.services.ldap_service import LDAPConnectionError
from app.services.role_service import RoleService
from app.services import ldap_service

router = APIRouter(prefix="/admin", tags=["admin"])


class UserSummary(BaseModel):
    """Lightweight user summary accessible to any authenticated user for pickers/selectors."""
    id: str
    full_name: str | None
    email: str


@router.get("/users/summary", response_model=list[UserSummary], tags=["admin"])
def list_users_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return a minimal id/name list for all active users. Used by AssigneeSelector dropdowns."""
    users = AdminUserService(db).list_users()
    return [
        UserSummary(id=str(u.id), full_name=u.full_name, email=u.email)
        for u in users
        if u.is_active
    ]


@router.get("/users", response_model=list[AdminUserRead])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permissions_dependency(Permission.admin_manage_users)
    ),
):
    users = AdminUserService(db).list_users()
    return [
        AdminUserRead(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            roles=user.role_names,
            is_active=user.is_active,
            auth_provider=user.auth_provider,
            must_change_password=user.must_change_password,
        )
        for user in users
    ]


@router.post("/users", response_model=AdminUserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: AdminUserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permissions_dependency(Permission.admin_manage_users)
    ),
):
    user = AdminUserService(db).create_user(
        actor_user=current_user,
        email=payload.email,
        full_name=payload.full_name,
        password=payload.password,
        role_ids=payload.role_ids,
    )
    return AdminUserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        roles=user.role_names,
        is_active=user.is_active,
        auth_provider=user.auth_provider,
        must_change_password=user.must_change_password,
    )


@router.patch("/users/{user_id}/roles", response_model=AdminUserRead)
def update_user_roles(
    user_id: UUID,
    payload: AdminUserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permissions_dependency(Permission.admin_manage_users)
    ),
):
    user = AdminUserService(db).update_user_roles(
        actor_user=current_user,
        user_id=user_id,
        role_ids=payload.role_ids,
    )
    return AdminUserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        roles=user.role_names,
        is_active=user.is_active,
        auth_provider=user.auth_provider,
        must_change_password=user.must_change_password,
    )


@router.post("/users/{user_id}/reset-password", response_model=AdminUserRead)
def reset_user_password(
    user_id: UUID,
    payload: AdminPasswordResetRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permissions_dependency(Permission.admin_manage_users)
    ),
):
    user = AdminUserService(db).reset_user_password(
        actor_user=current_user,
        user_id=user_id,
        new_password=payload.new_password,
    )
    return AdminUserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        roles=user.role_names,
        is_active=user.is_active,
        auth_provider=user.auth_provider,
        must_change_password=user.must_change_password,
    )


@router.patch("/users/{user_id}/status", response_model=AdminUserRead)
def update_user_status(
    user_id: UUID,
    payload: AdminUserStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permissions_dependency(Permission.admin_manage_users)
    ),
):
    user = AdminUserService(db).update_user_status(
        actor_user=current_user,
        user_id=user_id,
        is_active=payload.is_active,
    )
    return AdminUserRead(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        roles=user.role_names,
        is_active=user.is_active,
        auth_provider=user.auth_provider,
        must_change_password=user.must_change_password,
    )


@router.get("/roles", response_model=list[RoleRead])
def list_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permissions_dependency(Permission.admin_manage_users)
    ),
):
    roles = RoleService(db).list_roles()
    return [
        RoleRead(
            id=role.id,
            name=role.name,
            description=role.description,
            permissions=[
                rp.permission.key for rp in role.permissions if rp.permission is not None
            ],
        )
        for role in roles
    ]


@router.post("/roles", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
def create_role(
    payload: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permissions_dependency(Permission.admin_manage_users)
    ),
):
    role = RoleService(db).create_role(
        actor_user=current_user,
        name=payload.name,
        description=payload.description,
    )
    return RoleRead(
        id=role.id,
        name=role.name,
        description=role.description,
        permissions=[
            rp.permission.key for rp in role.permissions if rp.permission is not None
        ],
    )


@router.patch("/roles/{role_id}", response_model=RoleRead)
def update_role(
    role_id: UUID,
    payload: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permissions_dependency(Permission.admin_manage_users)
    ),
):
    role = RoleService(db).update_role(
        actor_user=current_user,
        role_id=role_id,
        name=payload.name,
        description=payload.description,
    )
    return RoleRead(
        id=role.id,
        name=role.name,
        description=role.description,
        permissions=[
            rp.permission.key for rp in role.permissions if rp.permission is not None
        ],
    )


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_role(
    role_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permissions_dependency(Permission.admin_manage_users)
    ),
):
    RoleService(db).delete_role(
        actor_user=current_user,
        role_id=role_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/roles/{role_id}/permissions", response_model=RoleRead)
def update_role_permissions(
    role_id: UUID,
    payload: RolePermissionsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permissions_dependency(Permission.admin_manage_users)
    ),
):
    role = RoleService(db).update_role_permissions(
        actor_user=current_user,
        role_id=role_id,
        permission_ids=payload.permission_ids,
    )
    return RoleRead(
        id=role.id,
        name=role.name,
        description=role.description,
        permissions=[
            rp.permission.key for rp in role.permissions if rp.permission is not None
        ],
    )


@router.get("/ldap/status")
def ldap_status(
    current_user: User = Depends(
        require_permissions_dependency(Permission.admin_manage_users)
    ),
):
    return ldap_service.test_connection()


class LDAPTestPayload(BaseModel):
    email: str
    password: str


@router.post("/ldap/test")
def ldap_test_credentials(
    payload: LDAPTestPayload,
    current_user: User = Depends(
        require_permissions_dependency(Permission.admin_manage_users)
    ),
):
    try:
        result = ldap_service.authenticate_user(payload.email, payload.password)
    except LDAPConnectionError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    if result is None:
        return {"success": False, "message": "Credentials not accepted by LDAP"}
    return {"success": True, "email": result["email"], "full_name": result["full_name"]}


class LDAPSyncPayload(BaseModel):
    search: str = ""
    role_ids: list[UUID] = []


@router.post("/ldap/sync")
def ldap_sync_users(
    payload: LDAPSyncPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permissions_dependency(Permission.admin_manage_users)
    ),
):
    try:
        result = AdminUserService(db).sync_ldap_users(
            actor_user=current_user,
            search=payload.search,
            role_ids=payload.role_ids or None,
        )
    except LDAPConnectionError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    return result


@router.get("/permissions", response_model=list[PermissionRead])
def list_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permissions_dependency(Permission.admin_manage_users)
    ),
):
    permissions = RoleService(db).list_permissions()
    return [
        PermissionRead(
            id=permission.id,
            key=permission.key,
            description=permission.description,
        )
        for permission in permissions
    ]