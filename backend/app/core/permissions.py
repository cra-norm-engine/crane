from __future__ import annotations

from enum import StrEnum

from fastapi import HTTPException, status

ROLE_ADMIN = "admin"
ROLE_CYBERSECURITY_ENGINEER = "cybersecurity_engineer"
ROLE_DEVELOPMENT_TEAM = "development_team"
ROLE_PRODUCT_OWNER = "product_owner"
ROLE_LIFECYCLE_MANAGER = "lifecycle_manager"
ROLE_LEGAL_TEAM = "legal_team"
ROLE_PRODUCT_MANAGEMENT = "product_management"

ALL_ROLES = {
    ROLE_ADMIN,
    ROLE_CYBERSECURITY_ENGINEER,
    ROLE_DEVELOPMENT_TEAM,
    ROLE_PRODUCT_OWNER,
    ROLE_LIFECYCLE_MANAGER,
    ROLE_LEGAL_TEAM,
    ROLE_PRODUCT_MANAGEMENT,
}


class Permission(StrEnum):
    product_read = "product_read"
    product_write = "product_write"
    release_read = "release_read"
    release_write = "release_write"
    audit_read = "audit_read"
    authority_package_generate = "authority_package_generate"
    admin_manage_users = "admin_manage_users"


ROLE_PERMISSIONS: dict[str, set[Permission]] = {
    ROLE_ADMIN: set(Permission),
    ROLE_CYBERSECURITY_ENGINEER: {
        Permission.product_read,
        Permission.product_write,
        Permission.release_read,
        Permission.release_write,
        Permission.audit_read,
        Permission.authority_package_generate,
    },
    ROLE_DEVELOPMENT_TEAM: {
        Permission.product_read,
        Permission.release_read,
        Permission.release_write,
    },
    ROLE_PRODUCT_OWNER: {
        Permission.product_read,
        Permission.product_write,
        Permission.release_read,
    },
    ROLE_LIFECYCLE_MANAGER: {
        Permission.product_read,
        Permission.release_read,
        Permission.release_write,
    },
    ROLE_LEGAL_TEAM: {
        Permission.product_read,
        Permission.release_read,
        Permission.audit_read,
        Permission.authority_package_generate,
    },
    ROLE_PRODUCT_MANAGEMENT: {
        Permission.product_read,
        Permission.release_read,
    },
}


def get_permissions_for_roles(roles: list[str]) -> set[Permission]:
    permissions: set[Permission] = set()
    for role in roles:
        permissions |= ROLE_PERMISSIONS.get(role, set())
    return permissions


def require_permissions(user_roles: list[str], required_permissions: set[Permission]) -> None:
    effective_permissions = get_permissions_for_roles(user_roles)
    if not required_permissions.issubset(effective_permissions):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )