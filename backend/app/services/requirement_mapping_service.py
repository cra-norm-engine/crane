from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit_log_event import AuditLogEvent
from app.models.enums import AuditActionType, AuditStatus, EntityType
from app.models.requirement_mapping import RequirementMapping
from app.repositories.annex_requirement_repository import AnnexRequirementRepository
from app.repositories.requirement_mapping_repository import RequirementMappingRepository
from app.repositories.risk_item_repository import RiskItemRepository
from app.schemas.requirement_mapping import RequirementMappingCreate, RequirementMappingUpdate


class RequirementMappingService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.requirement_mapping_repository = RequirementMappingRepository(db)
        self.annex_requirement_repository = AnnexRequirementRepository(db)
        self.risk_item_repository = RiskItemRepository(db)

    def list(
        self,
        *,
        risk_item_id: UUID | None = None,
        annex_requirement_id: UUID | None = None,
        matrix: bool = False,
    ) -> list[RequirementMapping]:
        if matrix:
            return list(self.requirement_mapping_repository.list_for_matrix())
        if risk_item_id is not None:
            return list(self.requirement_mapping_repository.list_by_risk_item(risk_item_id))
        if annex_requirement_id is not None:
            return list(self.requirement_mapping_repository.list_by_annex_requirement(annex_requirement_id))
        return list(self.requirement_mapping_repository.list_for_matrix())

    def get(self, mapping_id: UUID) -> RequirementMapping:
        mapping = self.requirement_mapping_repository.get_with_relations(mapping_id)
        if mapping is None:
            raise ValueError("Requirement mapping not found.")
        return mapping

    def create(
        self,
        payload: RequirementMappingCreate,
        *,
        actor_user_id: UUID | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> RequirementMapping:
        annex_requirement = self.annex_requirement_repository.get_by_id(payload.annex_requirement_id)
        if annex_requirement is None:
            raise ValueError("Annex requirement not found.")

        if payload.risk_item_id is not None:
            risk_item = self.risk_item_repository.get_by_id(payload.risk_item_id)
            if risk_item is None:
                raise ValueError("Risk item not found.")

        mapping = RequirementMapping(
            risk_item_id=payload.risk_item_id,
            annex_requirement_id=payload.annex_requirement_id,
            engineering_requirement_ref=payload.engineering_requirement_ref,
            sdl_activity=payload.sdl_activity,
            implementation_status=payload.implementation_status,
            evidence_summary=payload.evidence_summary,
        )
        mapping = self.requirement_mapping_repository.add(mapping)

        self._write_audit_log(
            actor_user_id=actor_user_id,
            action_type=AuditActionType.create,
            entity_type=EntityType.requirement_mapping,
            entity_id=mapping.id,
            status=AuditStatus.success,
            ip_address=ip_address,
            user_agent=user_agent,
            details_json=self._snapshot(mapping),
        )

        self.db.commit()
        self.db.refresh(mapping)
        return mapping

    def update(
        self,
        mapping_id: UUID,
        payload: RequirementMappingUpdate,
        *,
        actor_user_id: UUID | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> RequirementMapping:
        mapping = self.get(mapping_id)
        before = self._snapshot(mapping)

        update_data = payload.model_dump(exclude_unset=True)

        if "annex_requirement_id" in update_data and update_data["annex_requirement_id"] is not None:
            annex_requirement = self.annex_requirement_repository.get_by_id(update_data["annex_requirement_id"])
            if annex_requirement is None:
                raise ValueError("Annex requirement not found.")

        if "risk_item_id" in update_data and update_data["risk_item_id"] is not None:
            risk_item = self.risk_item_repository.get_by_id(update_data["risk_item_id"])
            if risk_item is None:
                raise ValueError("Risk item not found.")

        for field_name, value in update_data.items():
            setattr(mapping, field_name, value)

        self.db.flush()
        self.db.refresh(mapping)

        self._write_audit_log(
            actor_user_id=actor_user_id,
            action_type=AuditActionType.update,
            entity_type=EntityType.requirement_mapping,
            entity_id=mapping.id,
            status=AuditStatus.success,
            ip_address=ip_address,
            user_agent=user_agent,
            details_json={
                "before": before,
                "after": self._snapshot(mapping),
                "updated_fields": sorted(update_data.keys()),
            },
        )

        self.db.commit()
        self.db.refresh(mapping)
        return mapping

    def delete(
        self,
        mapping_id: UUID,
        *,
        actor_user_id: UUID | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        mapping = self.get(mapping_id)
        before = self._snapshot(mapping)

        self.requirement_mapping_repository.delete(mapping)

        self._write_audit_log(
            actor_user_id=actor_user_id,
            action_type=AuditActionType.delete,
            entity_type=EntityType.requirement_mapping,
            entity_id=mapping_id,
            status=AuditStatus.success,
            ip_address=ip_address,
            user_agent=user_agent,
            details_json={"deleted": before},
        )

        self.db.commit()

    def _snapshot(self, mapping: RequirementMapping) -> dict[str, Any]:
        return {
            "id": str(mapping.id),
            "risk_item_id": str(mapping.risk_item_id) if mapping.risk_item_id else None,
            "annex_requirement_id": str(mapping.annex_requirement_id),
            "engineering_requirement_ref": mapping.engineering_requirement_ref,
            "sdl_activity": mapping.sdl_activity,
            "implementation_status": mapping.implementation_status.value,
            "evidence_summary": mapping.evidence_summary,
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