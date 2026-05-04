from __future__ import annotations

from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import create_audit_event
from app.core.exceptions import ConflictException
from app.models.enums import AuditStatus, EntityType
from app.models.security_advisory import SecurityAdvisory
from app.repositories.product_release_repository import ProductReleaseRepository
from app.repositories.security_advisory_repository import SecurityAdvisoryRepository
from app.schemas.security_advisory import (
    SecurityAdvisoryCreate,
    SecurityAdvisoryRead,
    SecurityAdvisoryUpdate,
)


class SecurityAdvisoryService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = SecurityAdvisoryRepository(db)
        self.release_repository = ProductReleaseRepository(db)

    def list_security_advisories(
        self, *, product_release_id: UUID | None = None
    ) -> list[SecurityAdvisoryRead]:
        advisories = self.repository.list_all(product_release_id=product_release_id)
        return [SecurityAdvisoryRead.model_validate(a) for a in advisories]

    def get_security_advisory(self, advisory_id: UUID) -> SecurityAdvisoryRead:
        return SecurityAdvisoryRead.model_validate(self.repository.get_or_404(advisory_id))

    def create_security_advisory(
        self, payload: SecurityAdvisoryCreate, actor: object
    ) -> SecurityAdvisoryRead:
        release = self.release_repository.get_or_404(payload.product_release_id)

        # Detect duplicate advisory_id before attempting insert.
        if self.repository.get_by_advisory_id(payload.advisory_id) is not None:
            raise ConflictException(
                f"Advisory ID '{payload.advisory_id}' already exists"
            )

        advisory = SecurityAdvisory(**payload.model_dump())
        try:
            self.repository.add(advisory)
            create_audit_event(
                self.db,
                actor_user_id=getattr(actor, "id", None),
                action_type="security_advisory.created",
                entity_type=EntityType.security_advisory,
                entity_id=advisory.id,
                status=AuditStatus.success,
                details_json={
                    "product_release_id": str(advisory.product_release_id),
                    "product_id": str(release.product_id),
                    "advisory_id": advisory.advisory_id,
                    "status": advisory.status,
                },
            )
            self.db.commit()
            self.db.refresh(advisory)
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictException("Unable to create security advisory") from exc
        return SecurityAdvisoryRead.model_validate(advisory)

    def update_security_advisory(
        self, advisory_id: UUID, payload: SecurityAdvisoryUpdate, actor: object
    ) -> SecurityAdvisoryRead:
        advisory = self.repository.get_or_404(advisory_id)
        release = self.release_repository.get_or_404(advisory.product_release_id)
        updates = payload.model_dump(exclude_unset=True)
        for field, value in updates.items():
            setattr(advisory, field, value)
        try:
            self.db.flush()
            create_audit_event(
                self.db,
                actor_user_id=getattr(actor, "id", None),
                action_type="security_advisory.updated",
                entity_type=EntityType.security_advisory,
                entity_id=advisory.id,
                status=AuditStatus.success,
                details_json={
                    "product_id": str(release.product_id),
                    "advisory_id": advisory.advisory_id,
                    "updated_fields": sorted(updates.keys()),
                },
            )
            self.db.commit()
            self.db.refresh(advisory)
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictException("Unable to update security advisory") from exc
        return SecurityAdvisoryRead.model_validate(advisory)

    def delete_security_advisory(self, advisory_id: UUID, actor: object) -> None:
        advisory = self.repository.get_or_404(advisory_id)
        release = self.release_repository.get_or_404(advisory.product_release_id)
        self.repository.delete(advisory)
        create_audit_event(
            self.db,
            actor_user_id=getattr(actor, "id", None),
            action_type="security_advisory.deleted",
            entity_type=EntityType.security_advisory,
            entity_id=advisory_id,
            status=AuditStatus.success,
            details_json={
                "product_id": str(release.product_id),
                "advisory_id": advisory.advisory_id,
            },
        )
        self.db.commit()
