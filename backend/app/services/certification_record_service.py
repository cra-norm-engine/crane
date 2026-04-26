from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.audit import create_audit_event
from app.core.exceptions import NotFoundException
from app.models.certification_record import CertificationRecord
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
