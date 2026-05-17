from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.audit import create_audit_event
from app.core.exceptions import NotFoundException
from app.models.certification_record import CertificationRecord, CertificationRecordArtifactLink
from app.models.enums import AuditStatus, CertificationStatus, EntityType
from app.repositories.certification_record_repository import CertificationRecordRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.certification_record import (
    CertificationRecordCreate,
    CertificationRecordRead,
    CertificationRecordUpdate,
)


class CertificationRecordService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = CertificationRecordRepository(db)
        self.product_repository = ProductRepository(db)

    def list_records(
        self,
        *,
        product_id: UUID | None = None,
        status: CertificationStatus | None = None,
    ) -> list[CertificationRecordRead]:
        records = self.repository.list_all(product_id=product_id, status=status)
        return [CertificationRecordRead.model_validate(r) for r in records]

    def get_record(self, record_id: UUID) -> CertificationRecordRead:
        record = self.repository.get_or_404(record_id)
        return CertificationRecordRead.model_validate(record)

    def create_record(
        self,
        payload: CertificationRecordCreate,
        *,
        actor: object,
    ) -> CertificationRecordRead:
        self.product_repository.get_or_404(payload.product_id)

        record = CertificationRecord(**payload.model_dump())
        self.repository.add(record)

        create_audit_event(
            self.db,
            actor_user_id=getattr(actor, "id", None),
            action_type="create",
            entity_type=EntityType.certification_record,
            entity_id=record.id,
            status=AuditStatus.success,
            details_json={
                "product_id": str(payload.product_id),
                "certification_scheme": payload.certification_scheme,
                "certification_body_name": payload.certification_body_name,
            },
        )
        self.db.commit()
        self.db.refresh(record)
        return CertificationRecordRead.model_validate(record)

    def update_record(
        self,
        record_id: UUID,
        payload: CertificationRecordUpdate,
        *,
        actor: object,
    ) -> CertificationRecordRead:
        record = self.repository.get_or_404(record_id)

        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(record, field, value)

        create_audit_event(
            self.db,
            actor_user_id=getattr(actor, "id", None),
            action_type="update",
            entity_type=EntityType.certification_record,
            entity_id=record.id,
            status=AuditStatus.success,
            details_json=payload.model_dump(exclude_unset=True),
        )
        self.db.commit()
        self.db.refresh(record)
        return CertificationRecordRead.model_validate(record)

    def delete_record(self, record_id: UUID, *, actor: object) -> None:
        record = self.repository.get_or_404(record_id)

        create_audit_event(
            self.db,
            actor_user_id=getattr(actor, "id", None),
            action_type="delete",
            entity_type=EntityType.certification_record,
            entity_id=record.id,
            status=AuditStatus.success,
            details_json={"certificate_number": record.certificate_number},
        )
        self.repository.delete(record)
        self.db.commit()

    def attach_revision(
        self,
        record_id: UUID,
        artifact_revision_id: UUID,
        *,
        actor_user_id: UUID | None,
    ) -> CertificationRecordRead:
        """Attach an existing artifact revision to the certification record."""
        record = self.repository.get_or_404(record_id)

        link = CertificationRecordArtifactLink(
            certification_record_id=record.id,
            artifact_revision_id=artifact_revision_id,
            linked_by_user_id=actor_user_id,
        )
        self.db.add(link)
        create_audit_event(
            self.db,
            actor_user_id=actor_user_id,
            action_type="update",
            entity_type=EntityType.certification_record,
            entity_id=record.id,
            status=AuditStatus.success,
            details_json={"action": "evidence_attached", "revision_id": str(artifact_revision_id)},
        )
        self.db.commit()
        self.db.refresh(record)
        return CertificationRecordRead.model_validate(record)

    async def upload_and_attach_evidence(
        self,
        record_id: UUID,
        artifact_type: str,
        upload: object,
        *,
        actor_user_id: UUID | None,
        title: str,
        description: str | None = None,
        change_summary: str | None = None,
    ) -> CertificationRecord:
        """Upload a new artifact and attach it to the certification record."""
        from app.services.artifact_service import ArtifactService

        record = self.repository.get_or_404(record_id)
        artifact_service = ArtifactService(self.db)

        artifact = await artifact_service.upload_artifact(
            actor_user_id=actor_user_id,
            title=title,
            artifact_type=artifact_type,
            description=description,
            change_summary=change_summary,
            upload=upload,
        )

        # Attach the artifact's latest revision
        link = CertificationRecordArtifactLink(
            certification_record_id=record.id,
            artifact_revision_id=artifact.latest_revision.id,
            linked_by_user_id=actor_user_id,
        )
        self.db.add(link)
        create_audit_event(
            self.db,
            actor_user_id=actor_user_id,
            action_type="update",
            entity_type=EntityType.certification_record,
            entity_id=record.id,
            status=AuditStatus.success,
            details_json={
                "action": "evidence_uploaded_attached",
                "artifact_id": str(artifact.id),
            },
        )
        self.db.commit()
        self.db.refresh(record)
        return record

    def detach_revision(
        self,
        record_id: UUID,
        link_id: UUID,
        *,
        actor_user_id: UUID | None,
    ) -> CertificationRecordRead:
        """Remove an artifact revision from the certification record."""
        record = self.repository.get_or_404(record_id)

        link = self.db.query(CertificationRecordArtifactLink).filter_by(
            id=link_id,
            certification_record_id=record.id,
        ).first()
        if not link:
            raise NotFoundException("Evidence link not found.")

        self.db.delete(link)
        create_audit_event(
            self.db,
            actor_user_id=actor_user_id,
            action_type="update",
            entity_type=EntityType.certification_record,
            entity_id=record.id,
            status=AuditStatus.success,
            details_json={"action": "evidence_removed", "link_id": str(link_id)},
        )
        self.db.commit()
        self.db.refresh(record)
        return CertificationRecordRead.model_validate(record)
