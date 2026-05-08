"""
MarketActionService — CRA Art. 35 recall and withdrawal workflow.

Handles creation, updates, authority notification marking, and closure of
market actions.  When a market action is activated it also transitions the
linked ProductRelease to the matching ReleaseStatus (recalled / withdrawn).
"""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.audit import create_audit_event
from app.core.exceptions import NotFoundException, ConflictException
from app.models.enums import (
    AuditActionType,
    AuditStatus,
    EntityType,
    MarketActionStatus,
    MarketActionType,
    ReleaseStatus,
)
from app.models.market_action import MarketAction
from app.repositories.market_action_repository import MarketActionRepository
from app.repositories.product_release_repository import ProductReleaseRepository
from app.schemas.market_action import MarketActionCreate, MarketActionRead, MarketActionUpdate


class MarketActionService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = MarketActionRepository(db)
        self.release_repo = ProductReleaseRepository(db)

    def list_actions(
        self,
        *,
        product_release_id: UUID | None = None,
        action_type: MarketActionType | None = None,
        status: MarketActionStatus | None = None,
    ) -> list[MarketActionRead]:
        items = self.repo.list_all(
            product_release_id=product_release_id,
            action_type=action_type,
            status=status,
        )
        return [MarketActionRead.model_validate(i) for i in items]

    def get_action(self, action_id: UUID) -> MarketActionRead:
        return MarketActionRead.model_validate(self.repo.get_or_404(action_id))

    def create_action(
        self,
        payload: MarketActionCreate,
        *,
        actor: object,
    ) -> MarketActionRead:
        # Verify the release exists.
        release = self.release_repo.get_or_404(payload.product_release_id)

        action = MarketAction(
            product_release_id=payload.product_release_id,
            action_type=payload.action_type,
            status=MarketActionStatus.draft,
            reason=payload.reason,
            affected_scope=payload.affected_scope,
            corrective_action=payload.corrective_action,
            authority_reference_number=payload.authority_reference_number,
            user_notice_text=payload.user_notice_text,
            internal_notes=payload.internal_notes,
        )
        self.repo.add(action)

        create_audit_event(
            self.db,
            actor_user_id=getattr(actor, "id", None),
            action_type=AuditActionType.create,
            entity_type=EntityType.market_action,
            entity_id=action.id,
            status=AuditStatus.success,
            details_json={
                "action_type": action.action_type.value,
                "product_release_id": str(action.product_release_id),
            },
        )
        self.db.commit()
        self.db.refresh(action)
        return MarketActionRead.model_validate(action)

    def update_action(
        self,
        action_id: UUID,
        payload: MarketActionUpdate,
        *,
        actor: object,
    ) -> MarketActionRead:
        action = self.repo.get_or_404(action_id)

        if action.status == MarketActionStatus.closed:
            raise ConflictException("Cannot modify a closed market action.")

        update_data = payload.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(action, field, value)

        # When status transitions to active, set the release status to recalled/withdrawn.
        new_status = update_data.get("status")
        if new_status == MarketActionStatus.active:
            release = self.release_repo.get_or_404(action.product_release_id)
            target_release_status = (
                ReleaseStatus.recalled
                if action.action_type == MarketActionType.recall
                else ReleaseStatus.withdrawn
            )
            release.release_status = target_release_status
            self.db.flush()

        self.db.flush()
        create_audit_event(
            self.db,
            actor_user_id=getattr(actor, "id", None),
            action_type=AuditActionType.update,
            entity_type=EntityType.market_action,
            entity_id=action.id,
            status=AuditStatus.success,
            details_json={k: str(v) if v is not None else None for k, v in update_data.items()},
        )
        self.db.commit()
        self.db.refresh(action)
        return MarketActionRead.model_validate(action)

    def mark_authority_notified(
        self,
        action_id: UUID,
        *,
        actor: object,
        notified_at: datetime | None = None,
    ) -> MarketActionRead:
        action = self.repo.get_or_404(action_id)
        if action.status == MarketActionStatus.closed:
            raise ConflictException("Cannot update a closed market action.")

        action.authority_notified_at = notified_at or datetime.now(UTC)
        action.status = MarketActionStatus.authority_notified
        self.db.flush()

        create_audit_event(
            self.db,
            actor_user_id=getattr(actor, "id", None),
            action_type=AuditActionType.notify,
            entity_type=EntityType.market_action,
            entity_id=action.id,
            status=AuditStatus.success,
            details_json={"authority_notified_at": action.authority_notified_at.isoformat()},
        )
        self.db.commit()
        self.db.refresh(action)
        return MarketActionRead.model_validate(action)

    def close_action(
        self,
        action_id: UUID,
        *,
        actor: object,
    ) -> MarketActionRead:
        action = self.repo.get_or_404(action_id)
        if action.status == MarketActionStatus.closed:
            raise ConflictException("Market action is already closed.")

        action.status = MarketActionStatus.closed
        self.db.flush()

        create_audit_event(
            self.db,
            actor_user_id=getattr(actor, "id", None),
            action_type=AuditActionType.update,
            entity_type=EntityType.market_action,
            entity_id=action.id,
            status=AuditStatus.success,
            details_json={"status": "closed"},
        )
        self.db.commit()
        self.db.refresh(action)
        return MarketActionRead.model_validate(action)

    def delete_action(self, action_id: UUID, *, actor: object) -> None:
        action = self.repo.get_or_404(action_id)
        if action.status != MarketActionStatus.draft:
            raise ConflictException("Only draft market actions can be deleted.")

        self.repo.delete(action)
        create_audit_event(
            self.db,
            actor_user_id=getattr(actor, "id", None),
            action_type=AuditActionType.delete,
            entity_type=EntityType.market_action,
            entity_id=action_id,
            status=AuditStatus.success,
            details_json={},
        )
        self.db.commit()
