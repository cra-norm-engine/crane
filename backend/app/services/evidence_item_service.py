from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit_log_event import AuditLogEvent
from app.models.enums import AuditActionType, AuditStatus, EntityType
from app.models.evidence_item import EvidenceItem
from app.repositories.evidence_item_repository import EvidenceItemRepository
from app.schemas.evidence_item import EvidenceItemCreate, EvidenceItemUpdate


class EvidenceItemService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.evidence_item_repository = EvidenceItemRepository(db)

    def list(
        self,
        *,
        product_release_id: UUID | None = None,
        risk_assessment_id: UUID | None = None,
        requirement_mapping_id: UUID | None = None,
    ) -> list[EvidenceItem]:
        if requirement_mapping_id is not None:
            return list(self.evidence_item_repository.list_by_requirement_mapping(requirement_mapping_id))
        if risk_assessment_id is not None:
            return list(self.evidence_item_repository.list_by_risk_assessment(risk_assessment_id))
        if product_release_id is not None:
            return list(self.evidence_item_repository.list_by_product_release(product_release_id))
        raise ValueError(
            "One of product_release_id, risk_assessment_id, or requirement_mapping_id must be provided."
        )

    def get(self, evidence_item_id: UUID) -> EvidenceItem:
        evidence_item = self.evidence_item_repository.get_by_id(evidence_item_id)
        if evidence_item is None:
            raise ValueError("Evidence item not found.")
        return evidence_item

    def create(
        self,
        payload: EvidenceItemCreate,
        *,
        actor_user_id: UUID | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> EvidenceItem:
        evidence_item = EvidenceItem(
            product_release_id=payload.product_release_id,
            risk_assessment_id=payload.risk_assessment_id,
            requirement_mapping_id=payload.requirement_mapping_id,
            title=payload.title,
            description=payload.description,
            evidence_type=payload.evidence_type,
            file_path=payload.file_path,
            external_url=payload.external_url,
            uploaded_by_user_id=payload.uploaded_by_user_id,
        )
        evidence_item = self.evidence_item_repository.add(evidence_item)

        self._write_audit_log(
            actor_user_id=actor_user_id,
            action_type=AuditActionType.create,
            entity_type=EntityType.evidence_item,
            entity_id=evidence_item.id,
            status=AuditStatus.success,
            ip_address=ip_address,
            user_agent=user_agent,
            details_json=self._snapshot(evidence_item),
        )

        self.db.commit()
        self.db.refresh(evidence_item)
        return evidence_item

    def update(
        self,
        evidence_item_id: UUID,
        payload: EvidenceItemUpdate,
        *,
        actor_user_id: UUID | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> EvidenceItem:
        evidence_item = self.get(evidence_item_id)
        before = self._snapshot(evidence_item)

        update_data = payload.model_dump(exclude_unset=True)
        for field_name, value in update_data.items():
            setattr(evidence_item, field_name, value)

        if not any(
            [
                evidence_item.product_release_id,
                evidence_item.risk_assessment_id,
                evidence_item.requirement_mapping_id,
            ]
        ):
            raise ValueError(
                "At least one of product_release_id, risk_assessment_id, or requirement_mapping_id must be set."
            )

        self.db.flush()
        self.db.refresh(evidence_item)

        self._write_audit_log(
            actor_user_id=actor_user_id,
            action_type=AuditActionType.update,
            entity_type=EntityType.evidence_item,
            entity_id=evidence_item.id,
            status=AuditStatus.success,
            ip_address=ip_address,
            user_agent=user_agent,
            details_json={
                "before": before,
                "after": self._snapshot(evidence_item),
                "updated_fields": sorted(update_data.keys()),
            },
        )

        self.db.commit()
        self.db.refresh(evidence_item)
        return evidence_item

    def delete(
        self,
        evidence_item_id: UUID,
        *,
        actor_user_id: UUID | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        evidence_item = self.get(evidence_item_id)
        before = self._snapshot(evidence_item)

        self.evidence_item_repository.delete(evidence_item)

        self._write_audit_log(
            actor_user_id=actor_user_id,
            action_type=AuditActionType.delete,
            entity_type=EntityType.evidence_item,
            entity_id=evidence_item_id,
            status=AuditStatus.success,
            ip_address=ip_address,
            user_agent=user_agent,
            details_json={"deleted": before},
        )

        self.db.commit()

    def _snapshot(self, evidence_item: EvidenceItem) -> dict[str, Any]:
        return {
            "id": str(evidence_item.id),
            "product_release_id": str(evidence_item.product_release_id) if evidence_item.product_release_id else None,
            "risk_assessment_id": str(evidence_item.risk_assessment_id) if evidence_item.risk_assessment_id else None,
            "requirement_mapping_id": (
                str(evidence_item.requirement_mapping_id) if evidence_item.requirement_mapping_id else None
            ),
            "title": evidence_item.title,
            "description": evidence_item.description,
            "evidence_type": evidence_item.evidence_type.value,
            "file_path": evidence_item.file_path,
            "external_url": evidence_item.external_url,
            "uploaded_by_user_id": str(evidence_item.uploaded_by_user_id),
        }

    def _write_audit_log(
        self,
        *,
        actor_user_id: UUID | None,
        action_type: AuditActionType,
        entity_type: EntityType,
        entity_id: UUID | None,
        status: AuditStatus,
        details_json: dict[str, Any],
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        event = AuditLogEvent(
            actor_user_id=actor_user_id,
            action_type=action_type.value,
            entity_type=entity_type.value,
            entity_id=entity_id,
            status=status.value,
            ip_address=ip_address,
            user_agent=user_agent,
            details_json=details_json,
        )
        event.set_checksum()
        self.db.add(event)
        self.db.flush()