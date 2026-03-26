from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.audit import AuditLogger
from app.core.exceptions import ConflictException, NotFoundException
from app.models.enums import AuditStatus, EntityType
from app.models.user import User
from app.repositories.role_repository import RoleRepository


SYSTEM_ROLE_NAMES = {
    "admin",
    "cybersecurity_engineer",
    "development_team",
    "product_owner",
    "lifecycle_manager",
    "legal_team",
    "product_management",
}


class RoleService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.role_repository = RoleRepository(db)
        self.audit_logger = AuditLogger(db)

    def _validate_permission_ids(self, permission_ids: list[UUID]) -> None:
        for permission_id in permission_ids:
            permission = self.role_repository.get_permission_by_id(permission_id)
            if permission is None:
                raise NotFoundException(f"Permission not found: {permission_id}")

    def list_roles(self):
        return self.role_repository.list_roles()

    def list_permissions(self):
        return self.role_repository.list_permissions()

    def create_role(
        self,
        *,
        actor_user: User,
        name: str,
        description: str | None = None,
    ):
        existing = self.role_repository.get_by_name(name)
        if existing is not None:
            raise ConflictException("Role with this name already exists")

        role = self.role_repository.create_role(
            name=name,
            description=description,
        )

        self.audit_logger.log_event(
            actor_user_id=actor_user.id,
            action_type="admin.role.created",
            entity_type=EntityType.role.value,
            entity_id=role.id,
            status=AuditStatus.success.value,
            details_json={
                "name": role.name,
                "description": role.description,
            },
            commit=True,
        )

        return role

    def update_role(
        self,
        *,
        actor_user: User,
        role_id: UUID,
        name: str | None = None,
        description: str | None = None,
    ):
        role = self.role_repository.get_by_id(role_id)
        if role is None:
            raise NotFoundException("Role not found")

        if name is not None and name != role.name:
            existing = self.role_repository.get_by_name(name)
            if existing is not None and existing.id != role_id:
                raise ConflictException("Role with this name already exists")

        previous = {
            "name": role.name,
            "description": role.description,
        }

        updated_role = self.role_repository.update_role(
            role_id=role_id,
            name=name,
            description=description,
        )

        self.audit_logger.log_event(
            actor_user_id=actor_user.id,
            action_type="admin.role.updated",
            entity_type=EntityType.role.value,
            entity_id=role_id,
            status=AuditStatus.success.value,
            details_json={
                "before": previous,
                "after": {
                    "name": updated_role.name,
                    "description": updated_role.description,
                },
            },
            commit=True,
        )

        return updated_role

    def delete_role(
        self,
        *,
        actor_user: User,
        role_id: UUID,
    ) -> None:
        role = self.role_repository.get_by_id(role_id)
        if role is None:
            raise NotFoundException("Role not found")

        if role.name in SYSTEM_ROLE_NAMES:
            raise ConflictException("System roles cannot be deleted")

        self.role_repository.delete_role(role_id)

        self.audit_logger.log_event(
            actor_user_id=actor_user.id,
            action_type="admin.role.deleted",
            entity_type=EntityType.role.value,
            entity_id=role_id,
            status=AuditStatus.success.value,
            details_json={
                "name": role.name,
                "description": role.description,
            },
            commit=True,
        )

    def update_role_permissions(
        self,
        *,
        actor_user: User,
        role_id: UUID,
        permission_ids: list[UUID],
    ):
        role = self.role_repository.get_by_id(role_id)
        if role is None:
            raise NotFoundException("Role not found")

        self._validate_permission_ids(permission_ids)

        previous_permissions = sorted(
            rp.permission.key for rp in role.permissions if rp.permission is not None
        )

        updated_role = self.role_repository.set_role_permissions(role_id, permission_ids)

        updated_permissions = sorted(
            rp.permission.key for rp in updated_role.permissions if rp.permission is not None
        )

        self.audit_logger.log_event(
            actor_user_id=actor_user.id,
            action_type="admin.role.permissions_updated",
            entity_type=EntityType.role.value,
            entity_id=role_id,
            status=AuditStatus.success.value,
            details_json={
                "role_name": updated_role.name,
                "before_permissions": previous_permissions,
                "after_permissions": updated_permissions,
                "permission_ids": [str(pid) for pid in permission_ids],
            },
            commit=True,
        )

        return updated_role