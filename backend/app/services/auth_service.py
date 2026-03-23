from __future__ import annotations

from sqlalchemy.orm import Session

from app.core.audit import AuditLogger
from app.core.exceptions import AppException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_token_jti,
    get_token_subject,
    verify_password,
)
from app.models.enums import AuditActionType, AuditStatus, EntityType
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, TokenRead


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.user_repository = UserRepository(db)
        self.audit_logger = AuditLogger(db)

    def authenticate(self, payload: LoginRequest) -> TokenRead:
        return self.login(payload=payload)

    def login(
        self,
        *,
        payload: LoginRequest,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> TokenRead:
        user = self.user_repository.get_by_email(payload.email)

        if user is None or not verify_password(payload.password, user.hashed_password):
            self.audit_logger.log_event(
                actor_user_id=None,
                action_type=AuditActionType.failed_login.value,
                entity_type=EntityType.user.value,
                entity_id=None,
                status=AuditStatus.failure.value,
                ip_address=ip_address,
                user_agent=user_agent,
                details_json={"email": payload.email},
                commit=True,
            )
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

        access_token = create_access_token(
            str(user.id),
            extra_claims={"roles": user.role_names, "email": user.email},
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
            details_json={"email": user.email, "roles": user.role_names},
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

        new_access_token = create_access_token(
            str(user.id),
            extra_claims={"roles": user.role_names, "email": user.email},
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
            details_json={"email": user.email, "event": "token_refresh", "refresh_jti": refresh_jti},
            commit=True,
        )

        return TokenRead(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
        )

    def logout(
        self,
        *,
        user: User,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
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