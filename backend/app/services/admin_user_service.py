from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.audit import AuditLogger
from app.core.exceptions import ConflictException, NotFoundException
from app.core.security import hash_password
from app.models.enums import AuditStatus, EntityType
from app.models.user import User
from app.repositories.user_repository import UserRepository


class AdminUserService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.user_repository = UserRepository(db)
        self.audit_logger = AuditLogger(db)

    def _validate_role_ids(self, role_ids: list[UUID]) -> None:
        for role_id in role_ids:
            role = self.user_repository.get_role_by_id(role_id)
            if role is None:
                raise NotFoundException(f"Role not found: {role_id}")

    def create_user(
        self,
        *,
        actor_user: User,
        email: str,
        full_name: str,
        password: str,
        role_ids: list[UUID],
    ) -> User:
        existing = self.user_repository.get_by_email(email)
        if existing:
            raise ConflictException("User with this email already exists")

        self._validate_role_ids(role_ids)

        hashed_password = hash_password(password)

        user = self.user_repository.create_user(
            email=email,
            full_name=full_name,
            hashed_password=hashed_password,
            is_active=True,
        )

        if role_ids:
            user = self.user_repository.set_user_roles(user.id, role_ids)

        self.audit_logger.log_event(
            actor_user_id=actor_user.id,
            action_type="admin.user.created",
            entity_type=EntityType.user.value,
            entity_id=user.id,
            status=AuditStatus.success.value,
            details_json={
                "target_user_email": user.email,
                "target_user_full_name": user.full_name,
                "role_ids": [str(rid) for rid in role_ids],
                "after_roles": user.role_names,
                "is_active": user.is_active,
            },
            commit=True,
        )

        return user

    def update_user_roles(
        self,
        *,
        actor_user: User,
        user_id: UUID,
        role_ids: list[UUID],
    ) -> User:
        user = self.user_repository.get_by_id(user_id)
        if user is None:
            raise NotFoundException("User not found")

        self._validate_role_ids(role_ids)
        previous_roles = user.role_names

        updated_user = self.user_repository.set_user_roles(user_id, role_ids)

        self.audit_logger.log_event(
            actor_user_id=actor_user.id,
            action_type="admin.user.roles_updated",
            entity_type=EntityType.user.value,
            entity_id=user_id,
            status=AuditStatus.success.value,
            details_json={
                "target_user_email": updated_user.email,
                "target_user_full_name": updated_user.full_name,
                "before_roles": previous_roles,
                "after_roles": updated_user.role_names,
                "role_ids": [str(rid) for rid in role_ids],
            },
            commit=True,
        )

        return updated_user

    def update_user_status(
        self,
        *,
        actor_user: User,
        user_id: UUID,
        is_active: bool,
    ) -> User:
        user = self.user_repository.get_by_id(user_id)
        if user is None:
            raise NotFoundException("User not found")

        previous_status = user.is_active
        updated_user = self.user_repository.set_user_active(user_id, is_active)

        self.audit_logger.log_event(
            actor_user_id=actor_user.id,
            action_type="admin.user.activated" if is_active else "admin.user.deactivated",
            entity_type=EntityType.user.value,
            entity_id=user_id,
            status=AuditStatus.success.value,
            details_json={
                "target_user_email": updated_user.email,
                "target_user_full_name": updated_user.full_name,
                "before_is_active": previous_status,
                "after_is_active": updated_user.is_active,
            },
            commit=True,
        )

        return updated_user

    def list_users(self) -> list[User]:
        return self.user_repository.list_users()
