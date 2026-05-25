from __future__ import annotations

import logging
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import create_audit_event
from app.core.exceptions import ConflictException
from app.models.enums import AuditStatus, EntityType
from app.models.security_update import SecurityUpdate
from app.repositories.product_release_repository import ProductReleaseRepository
from app.repositories.security_update_repository import SecurityUpdateRepository
from app.schemas.security_update import SecurityUpdateCreate, SecurityUpdateRead, SecurityUpdateUpdate

logger = logging.getLogger(__name__)


class SecurityUpdateService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = SecurityUpdateRepository(db)
        self.product_release_repository = ProductReleaseRepository(db)

    def list_security_updates(
        self,
        *,
        product_release_id: UUID | None = None,
        product_id: UUID | None = None,
    ) -> list[SecurityUpdateRead]:
        updates = self.repository.list_all(
            product_release_id=product_release_id,
            product_id=product_id,
        )
        return [SecurityUpdateRead.model_validate(item) for item in updates]

    def get_security_update(self, security_update_id: UUID) -> SecurityUpdateRead:
        security_update = self.repository.get_or_404(security_update_id)
        return SecurityUpdateRead.model_validate(security_update)

    def create_security_update(self, payload: SecurityUpdateCreate, actor: object) -> SecurityUpdateRead:
        release = self.product_release_repository.get_or_404(payload.product_release_id)

        security_update = SecurityUpdate(**payload.model_dump())

        try:
            self.repository.add(security_update)
            create_audit_event(
                self.db,
                actor_user_id=getattr(actor, "id", None),
                action_type="security_update.created",
                entity_type=EntityType.security_update,
                entity_id=security_update.id,
                status=AuditStatus.success,
                details_json={
                    "product_release_id": str(security_update.product_release_id),
                    "product_id": str(release.product_id),
                    "title": security_update.title,
                    "release_version": f"v{release.system_version}",
                    "distribution_mechanism": security_update.distribution_mechanism.value,
                },
            )
            self.db.commit()
            self.db.refresh(security_update)
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictException("Unable to create security update due to constraint conflict") from exc

        # Auto-generate lifecycle notifications for support period recipients.
        try:
            from app.services.lifecycle_notification_service import LifecycleNotificationService
            LifecycleNotificationService(self.db).create_security_update_notifications(
                security_update.id, actor=actor
            )
        except Exception:
            logger.exception(
                "Failed to create security update lifecycle notifications for update %s",
                security_update.id,
            )

        return SecurityUpdateRead.model_validate(security_update)

    def update_security_update(
        self,
        security_update_id: UUID,
        payload: SecurityUpdateUpdate,
        actor: object,
    ) -> SecurityUpdateRead:
        security_update = self.repository.get_or_404(security_update_id)
        updates = payload.model_dump(exclude_unset=True)
        release = self.product_release_repository.get_or_404(security_update.product_release_id)

        for field_name, value in updates.items():
            setattr(security_update, field_name, value)

        try:
            self.db.flush()
            create_audit_event(
                self.db,
                actor_user_id=getattr(actor, "id", None),
                action_type="security_update.updated",
                entity_type=EntityType.security_update,
                entity_id=security_update.id,
                status=AuditStatus.success,
                details_json={
                    "product_id": str(release.product_id),
                    "product_release_id": str(security_update.product_release_id),
                    "release_version": f"v{release.system_version}",
                    "title": security_update.title,
                    "updated_fields": sorted(updates.keys()),
                },
            )
            self.db.commit()
            self.db.refresh(security_update)
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictException("Unable to update security update due to constraint conflict") from exc

        return SecurityUpdateRead.model_validate(security_update)

    def delete_security_update(self, security_update_id: UUID, actor: object) -> None:
        security_update = self.repository.get_or_404(security_update_id)
        release = self.product_release_repository.get_or_404(security_update.product_release_id)
        self.repository.delete(security_update)
        create_audit_event(
            self.db,
            actor_user_id=getattr(actor, "id", None),
            action_type="security_update.deleted",
            entity_type=EntityType.security_update,
            entity_id=security_update.id,
            status=AuditStatus.success,
            details_json={
                "product_id": str(release.product_id),
                "product_release_id": str(security_update.product_release_id),
                "release_version": f"v{release.system_version}",
                "title": security_update.title,
            },
        )
        self.db.commit()
