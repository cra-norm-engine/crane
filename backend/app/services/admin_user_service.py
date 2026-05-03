from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.audit import AuditLogger
from app.core.exceptions import AppException, ConflictException, NotFoundException
from app.core.security import hash_password
from app.models.enums import AuthProvider, AuditStatus, EntityType
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.services import ldap_service
from app.services.ldap_service import LDAPConnectionError


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
            must_change_password=True,
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

    def reset_user_password(
        self,
        *,
        actor_user: User,
        user_id: UUID,
        new_password: str,
    ) -> User:
        user = self.user_repository.get_by_id(user_id)
        if user is None:
            raise NotFoundException("User not found")

        if user.auth_provider != AuthProvider.local:
            raise AppException("Password reset is not available for LDAP accounts", status_code=400)

        hashed = hash_password(new_password)
        updated_user = self.user_repository.set_password(user_id, hashed, must_change_password=True)

        self.audit_logger.log_event(
            actor_user_id=actor_user.id,
            action_type="admin.user.password_reset",
            entity_type=EntityType.user.value,
            entity_id=user_id,
            status=AuditStatus.success.value,
            details_json={
                "target_user_email": updated_user.email,
                "target_user_full_name": updated_user.full_name,
            },
            commit=True,
        )
        return updated_user

    def list_users(self) -> list[User]:
        return self.user_repository.list_users()

    def sync_ldap_users(
        self,
        *,
        actor_user: User,
        search: str = "",
        role_ids: list[UUID] | None = None,
    ) -> dict:
        """
        Import LDAP users into the local DB (JIT-style, triggered manually by admin).
        Returns counts of {created, skipped, total}.
        Raises LDAPConnectionError when the server cannot be reached.
        """
        try:
            ldap_users = ldap_service.search_users(search)
        except LDAPConnectionError:
            raise

        created = 0
        skipped = 0

        for lu in ldap_users:
            email = lu["email"]
            existing = self.user_repository.get_by_email(email)
            if existing:
                skipped += 1
                continue

            user = self.user_repository.create_user(
                email=email,
                full_name=lu["full_name"],
                hashed_password=hash_password(""),
                is_active=True,
                auth_provider=AuthProvider.ldap,
            )

            if role_ids:
                self._validate_role_ids(role_ids)
                user = self.user_repository.set_user_roles(user.id, role_ids)

            self.audit_logger.log_event(
                actor_user_id=actor_user.id,
                action_type="admin.user.ldap_synced",
                entity_type=EntityType.user.value,
                entity_id=user.id,
                status=AuditStatus.success.value,
                details_json={
                    "target_user_email": email,
                    "target_user_full_name": lu["full_name"],
                    "role_ids": [str(r) for r in (role_ids or [])],
                },
                commit=False,
            )
            created += 1

        self.db.commit()
        return {"created": created, "skipped": skipped, "total": len(ldap_users)}
