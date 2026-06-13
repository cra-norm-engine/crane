# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
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
from app.models.audit_log_event import AuditLogEvent
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

    def _count_recent_failed_logins(
        self,
        *,
        cutoff: datetime,
        email: str | None = None,
        ip_address: str | None = None,
    ) -> int:
        """Count failed_login audit events since ``cutoff`` for an account and/or IP."""
        stmt = (
            select(func.count())
            .select_from(AuditLogEvent)
            .where(
                AuditLogEvent.action_type == AuditActionType.failed_login.value,
                AuditLogEvent.occurred_at >= cutoff,
            )
        )
        if email is not None:
            stmt = stmt.where(AuditLogEvent.details_json["email"].astext == email)
        if ip_address is not None:
            stmt = stmt.where(AuditLogEvent.ip_address == ip_address)
        return self.db.scalar(stmt) or 0

    def _enforce_login_rate_limit(self, email: str, ip_address: str | None) -> None:
        """Reject login attempts once recent failures exceed the configured thresholds.

        Brute-force / credential-stuffing protection (pentest finding M-02). Failures
        are counted from the tamper-evident audit log over a rolling window, so the
        control is shared across all workers/instances and needs no extra storage.
        Fails open: a query error must never block legitimate logins.
        """
        window = settings.login_failure_window_minutes
        per_account = settings.login_max_failures_per_account
        per_ip = settings.login_max_failures_per_ip
        if window <= 0 or (per_account <= 0 and per_ip <= 0):
            return

        cutoff = datetime.now(UTC) - timedelta(minutes=window)
        try:
            account_failures = (
                self._count_recent_failed_logins(cutoff=cutoff, email=email)
                if per_account > 0
                else 0
            )
            ip_failures = (
                self._count_recent_failed_logins(cutoff=cutoff, ip_address=ip_address)
                if per_ip > 0 and ip_address
                else 0
            )
        except Exception:
            log.exception("Login rate-limit check failed; allowing attempt to proceed")
            return

        throttled = (per_account > 0 and account_failures >= per_account) or (
            per_ip > 0 and ip_failures >= per_ip
        )
        if throttled:
            log.warning(
                "Login throttled: email=%s ip=%s account_failures=%d ip_failures=%d window=%dm",
                email,
                ip_address,
                account_failures,
                ip_failures,
                window,
            )
            raise AppException(
                "Too many failed login attempts. Please wait a few minutes and try again.",
                status_code=429,
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

        # Brute-force / credential-stuffing protection (M-02): block before doing
        # any credential check once recent failures exceed the configured limits.
        self._enforce_login_rate_limit(email_lower, ip_address)

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
                "ver": user.token_version,
            },
        )
        refresh_token = create_refresh_token(
            str(user.id),
            extra_claims={"ver": user.token_version},
        )

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

        # Reuse detection: a refresh JTI that is already blocklisted was rotated out
        # or logged out. Re-presentation signals theft → kill the whole token family
        # (bump token_version) and refuse (M-04).
        if self.db.get(RevokedToken, refresh_jti) is not None:
            self.user_repository.bump_token_version(user.id)
            self.audit_logger.log_event(
                actor_user_id=user.id,
                action_type=AuditActionType.failed_login.value,
                entity_type=EntityType.user.value,
                entity_id=user.id,
                status=AuditStatus.failure.value,
                ip_address=ip_address,
                user_agent=user_agent,
                details_json={
                    "email": user.email,
                    "reason": "refresh_token_reuse_detected",
                    "refresh_jti": refresh_jti,
                },
                commit=True,
            )
            raise AppException("Refresh token has been revoked", status_code=401)

        # Reject refresh tokens minted before the user's token_version was bumped
        # (e.g. after a password change or a prior reuse event).
        if payload.get("ver", 0) != user.token_version:
            raise AppException("Refresh token has been invalidated", status_code=401)

        # Rotation: blocklist the presented refresh token so it can be used only once,
        # then mint a fresh refresh token below.
        refresh_exp = payload.get("exp")
        if refresh_exp:
            self.db.merge(
                RevokedToken(
                    jti=refresh_jti,
                    expires_at=datetime.fromtimestamp(refresh_exp, tz=UTC),
                )
            )

        permissions = sorted(permission.value for permission in get_permissions_from_user(user))

        new_access_token = create_access_token(
            str(user.id),
            extra_claims={
                "roles": user.role_names,
                "permissions": permissions,
                "email": user.email,
                "ver": user.token_version,
            },
        )
        new_refresh_token = create_refresh_token(
            str(user.id),
            extra_claims={"ver": user.token_version},
        )

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
        refresh_token: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        # Revoke the current access token so it cannot be reused after logout.
        jti = access_token_payload.get("jti")
        exp = access_token_payload.get("exp")
        if jti and exp:
            expires_at = datetime.fromtimestamp(exp, tz=UTC)
            self.db.merge(RevokedToken(jti=jti, expires_at=expires_at))

        # Also revoke the refresh token (when the client supplies it) so it cannot
        # mint new access tokens after logout (M-04). Best-effort: never fail logout
        # because of a malformed token.
        if refresh_token:
            try:
                refresh_payload = decode_refresh_token(refresh_token)
                refresh_jti = refresh_payload.get("jti")
                refresh_exp = refresh_payload.get("exp")
                if refresh_jti and refresh_exp:
                    self.db.merge(
                        RevokedToken(
                            jti=refresh_jti,
                            expires_at=datetime.fromtimestamp(refresh_exp, tz=UTC),
                        )
                    )
            except Exception:
                log.warning("Could not decode refresh token during logout; skipping its revocation")

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