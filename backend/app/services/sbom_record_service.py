from __future__ import annotations

from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import create_audit_event
from app.core.exceptions import ConflictException
from app.models.enums import AuditStatus, EntityType
from app.models.sbom_record import SbomRecord
from app.repositories.product_release_repository import ProductReleaseRepository
from app.repositories.sbom_record_repository import SbomRecordRepository
from app.schemas.sbom_record import SbomRecordCreate, SbomRecordRead, SbomRecordUpdate


class SbomRecordService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = SbomRecordRepository(db)
        self.release_repository = ProductReleaseRepository(db)

    def list_sbom_records(
        self, *, product_release_id: UUID | None = None
    ) -> list[SbomRecordRead]:
        records = self.repository.list_all(product_release_id=product_release_id)
        return [SbomRecordRead.model_validate(r) for r in records]

    def get_sbom_record(self, sbom_id: UUID) -> SbomRecordRead:
        return SbomRecordRead.model_validate(self.repository.get_or_404(sbom_id))

    def create_sbom_record(self, payload: SbomRecordCreate, actor: object) -> SbomRecordRead:
        release = self.release_repository.get_or_404(payload.product_release_id)

        data = payload.model_dump()
        # Auto-derive component_count if not supplied but components_json is provided.
        if data.get("component_count") is None and data.get("components_json"):
            data["component_count"] = len(data["components_json"])

        record = SbomRecord(**data)
        try:
            self.repository.add(record)
            create_audit_event(
                self.db,
                actor_user_id=getattr(actor, "id", None),
                action_type="sbom_record.created",
                entity_type=EntityType.sbom_record,
                entity_id=record.id,
                status=AuditStatus.success,
                details_json={
                    "product_release_id": str(record.product_release_id),
                    "product_id": str(release.product_id),
                    "format": record.format,
                    "component_count": record.component_count,
                },
            )
            self.db.commit()
            self.db.refresh(record)
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictException("Unable to create SBOM record") from exc
        return SbomRecordRead.model_validate(record)

    def update_sbom_record(
        self, sbom_id: UUID, payload: SbomRecordUpdate, actor: object
    ) -> SbomRecordRead:
        record = self.repository.get_or_404(sbom_id)
        release = self.release_repository.get_or_404(record.product_release_id)
        updates = payload.model_dump(exclude_unset=True)

        # Keep component_count in sync when components_json is updated.
        if "components_json" in updates and updates.get("component_count") is None:
            updates["component_count"] = len(updates["components_json"])

        for field, value in updates.items():
            setattr(record, field, value)
        try:
            self.db.flush()
            create_audit_event(
                self.db,
                actor_user_id=getattr(actor, "id", None),
                action_type="sbom_record.updated",
                entity_type=EntityType.sbom_record,
                entity_id=record.id,
                status=AuditStatus.success,
                details_json={
                    "product_id": str(release.product_id),
                    "updated_fields": sorted(updates.keys()),
                },
            )
            self.db.commit()
            self.db.refresh(record)
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictException("Unable to update SBOM record") from exc
        return SbomRecordRead.model_validate(record)

    def delete_sbom_record(self, sbom_id: UUID, actor: object) -> None:
        record = self.repository.get_or_404(sbom_id)
        release = self.release_repository.get_or_404(record.product_release_id)
        self.repository.delete(record)
        create_audit_event(
            self.db,
            actor_user_id=getattr(actor, "id", None),
            action_type="sbom_record.deleted",
            entity_type=EntityType.sbom_record,
            entity_id=sbom_id,
            status=AuditStatus.success,
            details_json={"product_id": str(release.product_id), "format": record.format},
        )
        self.db.commit()
