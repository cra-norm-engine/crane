from __future__ import annotations

from enum import StrEnum
from typing import Callable, Iterable

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
    release_lifecycle_write = "release_lifecycle_write"

    remote_processing_element_read = "remote_processing_element_read"
    remote_processing_element_write = "remote_processing_element_write"

    scope_evaluation_read = "scope_evaluation_read"
    scope_evaluation_write = "scope_evaluation_write"

    risk_assessment_read = "risk_assessment_read"
    risk_assessment_write = "risk_assessment_write"

    risk_item_read = "risk_item_read"
    risk_item_write = "risk_item_write"

    annex_requirement_read = "annex_requirement_read"
    annex_requirement_write = "annex_requirement_write"

    requirement_mapping_read = "requirement_mapping_read"
    requirement_mapping_write = "requirement_mapping_write"

    evidence_item_read = "evidence_item_read"
    evidence_item_write = "evidence_item_write"

    audit_read = "audit_read"
    authority_package_generate = "authority_package_generate"
    admin_manage_users = "admin_manage_users"


ROLE_PERMISSIONS: dict[str, set[Permission]] = {
    ROLE_ADMIN: set(Permission),
    ROLE_CYBERSECURITY_ENGINEER: {
        Permission.product_read,
        Permission.release_read,
        Permission.remote_processing_element_read,
        Permission.remote_processing_element_write,
        Permission.scope_evaluation_read,
        Permission.scope_evaluation_write,
        Permission.risk_assessment_read,
        Permission.risk_assessment_write,
        Permission.risk_item_read,
        Permission.risk_item_write,
        Permission.annex_requirement_read,
        Permission.annex_requirement_write,
        Permission.requirement_mapping_read,
        Permission.requirement_mapping_write,
        Permission.evidence_item_read,
        Permission.evidence_item_write,
        Permission.audit_read,
    },
    ROLE_DEVELOPMENT_TEAM: {
        Permission.product_read,
        Permission.release_read,
        Permission.remote_processing_element_read,
    },
    ROLE_PRODUCT_OWNER: {
        Permission.product_read,
        Permission.product_write,
        Permission.release_read,
        Permission.release_write,
        Permission.remote_processing_element_read,
        Permission.remote_processing_element_write,
        Permission.scope_evaluation_read,
        Permission.risk_assessment_read,
        Permission.risk_item_read,
        Permission.annex_requirement_read,
        Permission.requirement_mapping_read,
        Permission.evidence_item_read,
    },
    ROLE_LIFECYCLE_MANAGER: {
        Permission.product_read,
        Permission.release_read,
        Permission.release_lifecycle_write,
        Permission.remote_processing_element_read,
        Permission.scope_evaluation_read,
        Permission.risk_assessment_read,
        Permission.risk_item_read,
        Permission.annex_requirement_read,
        Permission.requirement_mapping_read,
        Permission.evidence_item_read,
    },
    ROLE_LEGAL_TEAM: {
        Permission.product_read,
        Permission.release_read,
        Permission.remote_processing_element_read,
        Permission.scope_evaluation_read,
        Permission.risk_assessment_read,
        Permission.risk_item_read,
        Permission.annex_requirement_read,
        Permission.requirement_mapping_read,
        Permission.evidence_item_read,
    },
    ROLE_PRODUCT_MANAGEMENT: {
        Permission.product_read,
        Permission.product_write,
        Permission.release_read,
        Permission.release_write,
        Permission.remote_processing_element_read,
        Permission.remote_processing_element_write,
        Permission.scope_evaluation_read,
        Permission.risk_assessment_read,
        Permission.risk_item_read,
        Permission.annex_requirement_read,
        Permission.requirement_mapping_read,
        Permission.evidence_item_read,
    },
}


def normalize_role_names(roles: Iterable[str]) -> list[str]:
    normalized = []
    for role in roles:
        if role in ALL_ROLES:
            normalized.append(role)
    return normalized


def get_permissions_for_roles(roles: list[str]) -> set[Permission]:
    permissions: set[Permission] = set()
    for role in normalize_role_names(roles):
        permissions |= ROLE_PERMISSIONS.get(role, set())
    return permissions


def has_permissions(user_roles: list[str], required_permissions: set[Permission]) -> bool:
    effective_permissions = get_permissions_for_roles(user_roles)
    return required_permissions.issubset(effective_permissions)


def require_permissions(user_roles: list[str], required_permissions: set[Permission]) -> None:
    if not has_permissions(user_roles, required_permissions):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )


def require_roles(user_roles: list[str], required_roles: set[str]) -> None:
    effective_roles = set(normalize_role_names(user_roles))
    if not required_roles.intersection(effective_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient role privileges",
        )


def permission_dependency(*required_permissions: Permission) -> Callable[..., None]:
    required = set(required_permissions)

    def checker(current_user: object) -> None:
        user_roles = getattr(current_user, "role_names", [])
        require_permissions(user_roles, required)

    return checker


def role_dependency(*required_roles: str) -> Callable[..., None]:
    required = set(required_roles)

    def checker(current_user: object) -> None:
        user_roles = getattr(current_user, "role_names", [])
        require_roles(user_roles, required)

    return checker