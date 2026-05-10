from __future__ import annotations

import logging
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.core.audit import AuditLogger
from app.core.config import settings
from app.core.exceptions import AppException
from app.core.permissions import get_permissions_from_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_token_jti,
    get_token_subject,
    hash_password,
    verify_password,
)
from app.models.enums import AuthProvider, AuditActionType, AuditStatus, EntityType
from app.models.revoked_token import RevokedToken
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import ChangePasswordRequest, LoginRequest, TokenRead
from app.services import ldap_service
from app.services.ldap_service import LDAPConnectionError

log = logging.getLogger(__name__)


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.user_repository = UserRepository(db)
        self.audit_logger = AuditLogger(db)

    def authenticate(self, payload: LoginRequest) -> TokenRead:
        return self.login(payload=payload)

    def _log_failed_login(
        self,
        user_id,
        email: str,
        ip_address: str | None,
        user_agent: str | None,
    ) -> None:
        self.audit_logger.log_event(
            actor_user_id=user_id,
            action_type=AuditActionType.failed_login.value,
            entity_type=EntityType.user.value,
            entity_id=None,
            status=AuditStatus.failure.value,
            ip_address=ip_address,
            user_agent=user_agent,
            details_json={"email": email},
            commit=True,
        )

    def _jit_provision_ldap_user(self, email: str, full_name: str) -> User:
        """Create a local user record for an LDAP-authenticated user on first login."""
        user = self.user_repository.create_user(
            email=email,
            full_name=full_name,
            hashed_password=hash_password(""),  # unusable password — auth is via LDAP
            is_active=True,
            auth_provider=AuthProvider.ldap,
        )
        self.audit_logger.log_event(
            actor_user_id=user.id,
            action_type="admin.user.ldap_provisioned",
            entity_type=EntityType.user.value,
            entity_id=user.id,
            status=AuditStatus.success.value,
            details_json={"email": email, "full_name": full_name},
            commit=True,
        )
        return user

    def login(
        self,
        *,
        payload: LoginRequest,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> TokenRead:
        email_lower = payload.email.lower().strip()
        user = self.user_repository.get_by_email(email_lower)

        # --- LDAP path ---
        if settings.ldap_enabled and (user is None or user.auth_provider == AuthProvider.ldap):
            try:
                ldap_result = ldap_service.authenticate_user(email_lower, payload.password)
            except LDAPConnectionError as exc:
                log.error("LDAP server unreachable during login: %s", exc)
                raise AppException("Authentication service unavailable", status_code=503) from exc

            if ldap_result is None:
                self._log_failed_login(None, email_lower, ip_address, user_agent)
                raise AppException("Invalid email or password", status_code=401)

            # JIT provision on first successful LDAP login
            if user is None:
                user = self._jit_provision_ldap_user(
                    ldap_result["email"], ldap_result["full_name"]
                )
        else:
            # --- Local password path ---
            if user is None or not verify_password(payload.password, user.hashed_password):
                self._log_failed_login(None, email_lower, ip_address, user_agent)
                raise AppException("Invalid email or password", status_code=401)

        if not user.is_active:
            self.audit_logger.log_event(
                actor_user_id=user.id,
                action_type=AuditActionType.failed_login.value,
                entity_type=EntityType.user.value,
                entity_id=user.id,
                status=AuditStatus.failure.value,
                ip_address=ip_address,
                user_agent=user_agent,
                details_json={"email": user.email, "reason": "inactive_account"},
                commit=True,
            )
            raise AppException("User account is inactive", status_code=403)

        permissions = sorted(permission.value for permission in get_permissions_from_user(user))

        access_token = create_access_token(
            str(user.id),
            extra_claims={
                "roles": user.role_names,
                "permissions": permissions,
                "email": user.email,
            },
        )
        refresh_token = create_refresh_token(str(user.id))

        self.audit_logger.log_event(
            actor_user_id=user.id,
            action_type=AuditActionType.login.value,
            entity_type=EntityType.user.value,
            entity_id=user.id,
            status=AuditStatus.success.value,
            ip_address=ip_address,
            user_agent=user_agent,
            details_json={
                "email": user.email,
                "roles": user.role_names,
                "permissions": permissions,
            },
            commit=True,
        )

        return TokenRead(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
        )

    def refresh(
        self,
        *,
        refresh_token: str,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> TokenRead:
        payload = decode_refresh_token(refresh_token)
        user_id = get_token_subject(payload)
        refresh_jti = get_token_jti(payload)

        user = self.user_repository.get_by_id(user_id)
        if user is None or not user.is_active:
            self.audit_logger.log_event(
                actor_user_id=None,
                action_type=AuditActionType.failed_login.value,
                entity_type=EntityType.user.value,
                entity_id=None,
                status=AuditStatus.failure.value,
                ip_address=ip_address,
                user_agent=user_agent,
                details_json={"reason": "invalid_refresh_user", "refresh_jti": refresh_jti},
                commit=True,
            )
            raise AppException("User not found or inactive", status_code=401)

        permissions = sorted(permission.value for permission in get_permissions_from_user(user))

        new_access_token = create_access_token(
            str(user.id),
            extra_claims={
                "roles": user.role_names,
                "permissions": permissions,
                "email": user.email,
            },
        )
        new_refresh_token = create_refresh_token(str(user.id))

        self.audit_logger.log_event(
            actor_user_id=user.id,
            action_type=AuditActionType.login.value,
            entity_type=EntityType.user.value,
            entity_id=user.id,
            status=AuditStatus.success.value,
            ip_address=ip_address,
            user_agent=user_agent,
            details_json={
                "email": user.email,
                "event": "token_refresh",
                "refresh_jti": refresh_jti,
                "roles": user.role_names,
                "permissions": permissions,
            },
            commit=True,
        )

        return TokenRead(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
        )

    def change_password(
        self,
        *,
        user: User,
        payload: ChangePasswordRequest,
    ) -> None:
        if user.auth_provider != AuthProvider.local:
            raise AppException("Password changes are not available for LDAP accounts", status_code=400)

        if not verify_password(payload.current_password, user.hashed_password):
            raise AppException("Current password is incorrect", status_code=400)

        if payload.current_password == payload.new_password:
            raise AppException("New password must differ from the current password", status_code=400)

        new_hash = hash_password(payload.new_password)
        self.user_repository.set_password(user.id, new_hash, must_change_password=False)

        self.audit_logger.log_event(
            actor_user_id=user.id,
            action_type="auth.password_changed",
            entity_type=EntityType.user.value,
            entity_id=user.id,
            status=AuditStatus.success.value,
            details_json={"email": user.email},
            commit=True,
        )

    def logout(
        self,
        *,
        user: User,
        access_token_payload: dict,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        # Revoke the current access token so it cannot be reused after logout.
        jti = access_token_payload.get("jti")
        exp = access_token_payload.get("exp")
        if jti and exp:
            expires_at = datetime.fromtimestamp(exp, tz=UTC)
            self.db.merge(RevokedToken(jti=jti, expires_at=expires_at))

        self.audit_logger.log_event(
            actor_user_id=user.id,
            action_type=AuditActionType.logout.value,
            entity_type=EntityType.user.value,
            entity_id=user.id,
            status=AuditStatus.success.value,
            ip_address=ip_address,
            user_agent=user_agent,
            details_json={"email": user.email},
            commit=True,
        )