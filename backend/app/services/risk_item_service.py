from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit_log_event import AuditLogEvent
from app.models.enums import AuditActionType, AuditStatus, EntityType
from app.models.risk_item import RiskItem
from app.repositories.risk_item_repository import RiskItemRepository
from app.schemas.risk_item import RiskItemCreate, RiskItemUpdate


class RiskItemService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.risk_item_repository = RiskItemRepository(db)

    def list_by_assessment(self, risk_assessment_id: UUID) -> list[RiskItem]:
        return list(self.risk_item_repository.list_by_assessment(risk_assessment_id))

    def get(self, risk_item_id: UUID) -> RiskItem:
        risk_item = self.risk_item_repository.get_with_relations(risk_item_id)
        if risk_item is None:
            raise ValueError("Risk item not found.")
        return risk_item

    def create(
        self,
        payload: RiskItemCreate,
        *,
        actor_user_id: UUID | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> RiskItem:
        risk_item = RiskItem(
            risk_assessment_id=payload.risk_assessment_id,
            title=payload.title,
            description=payload.description,
            threat_scenario=payload.threat_scenario,
            asset_affected=payload.asset_affected,
            likelihood=payload.likelihood,
            impact=payload.impact,
            risk_level=payload.risk_level,
            mitigation_plan=payload.mitigation_plan,
            residual_risk_level=payload.residual_risk_level,
            status=payload.status,
            owner_user_id=payload.owner_user_id,
        )
        risk_item = self.risk_item_repository.add(risk_item)

        self._write_audit_log(
            actor_user_id=actor_user_id,
            action_type=AuditActionType.create,
            entity_type=EntityType.risk_item,
            entity_id=risk_item.id,
            status=AuditStatus.success,
            ip_address=ip_address,
            user_agent=user_agent,
            details_json={
                "risk_assessment_id": str(risk_item.risk_assessment_id),
                "title": risk_item.title,
                "risk_level": risk_item.risk_level.value,
                "status": risk_item.status.value,
            },
        )

        self.db.commit()
        self.db.refresh(risk_item)
        return risk_item

    def update(
        self,
        risk_item_id: UUID,
        payload: RiskItemUpdate,
        *,
        actor_user_id: UUID | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> RiskItem:
        risk_item = self.get(risk_item_id)

        before = self._snapshot(risk_item)
        update_data = payload.model_dump(exclude_unset=True)

        for field_name, value in update_data.items():
            setattr(risk_item, field_name, value)

        self.db.flush()
        self.db.refresh(risk_item)

        self._write_audit_log(
            actor_user_id=actor_user_id,
            action_type=AuditActionType.update,
            entity_type=EntityType.risk_item,
            entity_id=risk_item.id,
            status=AuditStatus.success,
            ip_address=ip_address,
            user_agent=user_agent,
            details_json={
                "before": before,
                "after": self._snapshot(risk_item),
                "updated_fields": sorted(update_data.keys()),
            },
        )

        self.db.commit()
        self.db.refresh(risk_item)
        return risk_item

    def delete(
        self,
        risk_item_id: UUID,
        *,
        actor_user_id: UUID | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        risk_item = self.get(risk_item_id)
        before = self._snapshot(risk_item)

        self.risk_item_repository.delete(risk_item)

        self._write_audit_log(
            actor_user_id=actor_user_id,
            action_type=AuditActionType.delete,
            entity_type=EntityType.risk_item,
            entity_id=risk_item_id,
            status=AuditStatus.success,
            ip_address=ip_address,
            user_agent=user_agent,
            details_json={"deleted": before},
        )

        self.db.commit()

    def _snapshot(self, risk_item: RiskItem) -> dict[str, Any]:
        return {
            "id": str(risk_item.id),
            "risk_assessment_id": str(risk_item.risk_assessment_id),
            "title": risk_item.title,
            "description": risk_item.description,
            "threat_scenario": risk_item.threat_scenario,
            "asset_affected": risk_item.asset_affected,
            "likelihood": risk_item.likelihood.value,
            "impact": risk_item.impact.value,
            "risk_level": risk_item.risk_level.value,
            "mitigation_plan": risk_item.mitigation_plan,
            "residual_risk_level": (
                risk_item.residual_risk_level.value if risk_item.residual_risk_level else None
            ),
            "status": risk_item.status.value,
            "owner_user_id": str(risk_item.owner_user_id) if risk_item.owner_user_id else None,
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