from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models.annex_requirement import AnnexRequirement
from app.models.audit_log_event import AuditLogEvent
from app.models.enums import AnnexPart, AuditActionType, AuditStatus, EntityType
from app.repositories.annex_requirement_repository import AnnexRequirementRepository
from app.schemas.annex_requirement import AnnexRequirementCreate, AnnexRequirementUpdate
from uuid import UUID


class AnnexRequirementService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.annex_requirement_repository = AnnexRequirementRepository(db)

    def list(
        self,
        *,
        is_active: bool | None = None,
        annex_part: AnnexPart | None = None,
    ) -> list[AnnexRequirement]:
        if annex_part is not None:
            items = list(self.annex_requirement_repository.list_by_part(annex_part))
            if is_active is None:
                return items
            return [item for item in items if item.is_active is is_active]

        if is_active is True:
            return list(self.annex_requirement_repository.list_active())

        return list(self.annex_requirement_repository.list_all())

    def get_by_id(self, requirement_id: UUID):
        requirement = self.annex_requirement_repository.get_by_id(requirement_id)
        if requirement is None:
            raise ValueError("Annex requirement not found.")
        return requirement

    def get_by_code(self, code: str) -> AnnexRequirement:
        requirement = self.annex_requirement_repository.get_by_code(code)
        if requirement is None:
            raise ValueError("Annex requirement not found.")
        return requirement

    def create(
        self,
        payload: AnnexRequirementCreate,
        *,
        actor_user_id: UUID | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AnnexRequirement:
        existing = self.annex_requirement_repository.get_by_code(payload.code)
        if existing is not None:
            raise ValueError(f"Annex requirement with code '{payload.code}' already exists.")

        requirement = AnnexRequirement(
            code=payload.code,
            title=payload.title,
            description=payload.description,
            annex_part=payload.annex_part,
            is_active=payload.is_active,
        )
        requirement = self.annex_requirement_repository.add(requirement)

        self._write_audit_log(
            actor_user_id=actor_user_id,
            action_type=AuditActionType.create,
            entity_type=EntityType.annex_requirement,
            entity_id=requirement.id,
            status=AuditStatus.success,
            ip_address=ip_address,
            user_agent=user_agent,
            details_json=self._snapshot(requirement),
        )

        self.db.commit()
        self.db.refresh(requirement)
        return requirement

    def update(
        self,
        requirement_id,
        payload: AnnexRequirementUpdate,
        *,
        actor_user_id : UUID | None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> AnnexRequirement:
        requirement = self.get_by_id(requirement_id)
        before = self._snapshot(requirement)

        update_data = payload.model_dump(exclude_unset=True)
        for field_name, value in update_data.items():
            setattr(requirement, field_name, value)

        self.db.flush()
        self.db.refresh(requirement)

        self._write_audit_log(
            actor_user_id=actor_user_id,
            action_type=AuditActionType.update,
            entity_type=EntityType.annex_requirement,
            entity_id=requirement.id,
            status=AuditStatus.success,
            ip_address=ip_address,
            user_agent=user_agent,
            details_json={
                "before": before,
                "after": self._snapshot(requirement),
                "updated_fields": sorted(update_data.keys()),
            },
        )

        self.db.commit()
        self.db.refresh(requirement)
        return requirement

    def _snapshot(self, requirement: AnnexRequirement) -> dict[str, Any]:
        return {
            "id": str(requirement.id),
            "code": requirement.code,
            "title": requirement.title,
            "description": requirement.description,
            "annex_part": requirement.annex_part.value,
            "is_active": requirement.is_active,
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