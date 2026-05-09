from __future__ import annotations

from enum import StrEnum
from typing import Callable

from fastapi import HTTPException, status

ROLE_ADMIN = "admin"
ROLE_CYBERSECURITY_ENGINEER = "cybersecurity_engineer"
ROLE_DEVELOPMENT_TEAM = "development_team"
ROLE_PRODUCT_OWNER = "product_owner"
ROLE_LIFECYCLE_MANAGER = "lifecycle_manager"
ROLE_LEGAL_TEAM = "legal_team"
ROLE_PRODUCT_MANAGEMENT = "product_management"


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

    support_period_read = "support_period_read"
    support_period_write = "support_period_write"
    security_update_read = "security_update_read"
    security_update_write = "security_update_write"
    lifecycle_notification_read = "lifecycle_notification_read"
    lifecycle_notification_write = "lifecycle_notification_write"

    audit_read = "audit_read"
    authority_package_generate = "authority_package_generate"
    admin_manage_users = "admin_manage_users"

    certification_record_read = "certification_record_read"
    certification_record_write = "certification_record_write"

    # Substantial change tracking
    # change_read  → view changes and assessments
    # change_write → initiate, submit, assess, and close changes
    change_read = "change_read"
    change_write = "change_write"

    # CRA Art. 35 — recall and withdrawal management
    market_action_read = "market_action_read"
    market_action_write = "market_action_write"

    # Threaded comments — attached to any entity in the system
    comment_read = "comment_read"
    comment_write = "comment_write"

def get_permissions_from_user(current_user: object) -> set[Permission]:
    permissions: set[Permission] = set()

    for user_role in getattr(current_user, "roles", []) or []:
        role = getattr(user_role, "role", None)
        if role is None:
            continue

        for role_permission in getattr(role, "permissions", []) or []:
            permission = getattr(role_permission, "permission", None)
            if permission is None or not getattr(permission, "key", None):
                continue

            try:
                permissions.add(Permission(permission.key))
            except ValueError:
                continue

    return permissions


def has_permissions(current_user: object, required_permissions: set[Permission]) -> bool:
    effective_permissions = get_permissions_from_user(current_user)
    return required_permissions.issubset(effective_permissions)


def require_permissions(current_user: object, required_permissions: set[Permission]) -> None:
    if not has_permissions(current_user, required_permissions):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )


def permission_dependency(*required_permissions: Permission) -> Callable[..., None]:
    required = set(required_permissions)

    def checker(current_user: object) -> None:
        require_permissions(current_user, required)

    return checker