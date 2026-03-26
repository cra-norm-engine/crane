from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.audit import create_audit_event
from app.models.enums import AuditActionType, AuditStatus, EntityType
from app.models.product import RemoteProcessingElement
from app.repositories.product_repository import ProductRepository
from app.repositories.remote_processing_element_repository import RemoteProcessingElementRepository
from app.schemas.remote_processing_element import (
    RemoteProcessingElementCreate,
    RemoteProcessingElementRead,
    RemoteProcessingElementUpdate,
)


class RemoteProcessingElementService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = RemoteProcessingElementRepository(db)
        self.product_repository = ProductRepository(db)

    def list_elements(self, *, product_id: UUID | None = None) -> list[RemoteProcessingElementRead]:
        elements = self.repository.list_all(product_id=product_id)
        return [RemoteProcessingElementRead.model_validate(element) for element in elements]

    def get_element(self, element_id: UUID) -> RemoteProcessingElementRead:
        element = self.repository.get_or_404(element_id)
        return RemoteProcessingElementRead.model_validate(element)

    def create_element(self, payload: RemoteProcessingElementCreate, actor: object) -> RemoteProcessingElementRead:
        self.product_repository.get_or_404(payload.product_id)

        element = RemoteProcessingElement(**payload.model_dump())
        self.repository.add(element)

        create_audit_event(
            self.db,
            actor_user_id=getattr(actor, "id", None),
            action_type=AuditActionType.create,
            entity_type=EntityType.remote_processing_element,
            entity_id=element.id,
            status=AuditStatus.success,
            details_json={
                "product_id": str(element.product_id),
                "name": element.name,
            },
        )
        self.db.commit()
        self.db.refresh(element)

        return RemoteProcessingElementRead.model_validate(element)

    def update_element(
        self,
        element_id: UUID,
        payload: RemoteProcessingElementUpdate,
        actor: object,
    ) -> RemoteProcessingElementRead:
        element = self.repository.get_or_404(element_id)
        updates = payload.model_dump(exclude_unset=True)

        for field_name, value in updates.items():
            setattr(element, field_name, value)

        self.db.flush()
        create_audit_event(
            self.db,
            actor_user_id=getattr(actor, "id", None),
            action_type=AuditActionType.update,
            entity_type=EntityType.remote_processing_element,
            entity_id=element.id,
            status=AuditStatus.success,
            details_json={"updated_fields": sorted(updates.keys())},
        )
        self.db.commit()
        self.db.refresh(element)

        return RemoteProcessingElementRead.model_validate(element)

    def delete_element(self, element_id: UUID, actor: object) -> None:
        element = self.repository.get_or_404(element_id)
        self.repository.delete(element)
        create_audit_event(
            self.db,
            actor_user_id=getattr(actor, "id", None),
            action_type=AuditActionType.delete,
            entity_type=EntityType.remote_processing_element,
            entity_id=element.id,
            status=AuditStatus.success,
            details_json={
                "product_id": str(element.product_id),
                "name": element.name,
            },
        )
        self.db.commit()