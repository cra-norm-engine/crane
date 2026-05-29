from __future__ import annotations

import logging
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.audit import create_audit_event
from app.models.enums import AuditActionType, AuditStatus, EntityType, RemoteProcessingClassification
from app.models.product import RemoteProcessingElement
from app.repositories.product_repository import ProductRepository
from app.repositories.remote_processing_element_repository import RemoteProcessingElementRepository
from app.schemas.remote_processing_element import (
    RemoteProcessingAssessRequest,
    RemoteProcessingElementCreate,
    RemoteProcessingElementRead,
    RemoteProcessingElementUpdate,
)

logger = logging.getLogger(__name__)


def _classify(p: RemoteProcessingAssessRequest) -> RemoteProcessingClassification:
    """Apply the DIGITALEUROPE I1/I3/I5/I6 inclusion criteria to classify the element.

    Classification logic (all four criteria must be True for in-scope):
      I1 False → third_party_component (not manufacturer-developed)
      I3 False → out_of_scope (ancillary/optional service)
      I5 False → out_of_scope (no direct product interaction)
      I6 False → out_of_scope (unidirectional data flow)
      All True → cra_art_3_2_in_scope
      Any None (unanswered) → not_assessed or requires_legal_assessment
    """
    if p.classification_override:
        return p.classification_override

    # I1: Designed/developed by or on behalf of the manufacturer.
    if p.is_developed_by_manufacturer is False:
        return RemoteProcessingClassification.third_party_component
    if p.is_developed_by_manufacturer is None:
        return RemoteProcessingClassification.not_assessed

    # I3: Necessary for the product to perform its functions.
    if p.is_necessary_for_product_function is False:
        return RemoteProcessingClassification.out_of_scope
    if p.is_necessary_for_product_function is None:
        return RemoteProcessingClassification.not_assessed

    # I5: Directly interacts with the product itself.
    if p.directly_interacts_with_product is False:
        return RemoteProcessingClassification.out_of_scope
    if p.directly_interacts_with_product is None:
        return RemoteProcessingClassification.not_assessed

    # I6: Bidirectional data exchange between product and RDPS.
    if p.has_bidirectional_exchange is False:
        return RemoteProcessingClassification.out_of_scope
    if p.has_bidirectional_exchange is None:
        return RemoteProcessingClassification.not_assessed

    # All four inclusion criteria are satisfied — element is a CRA Art. 3(2) RDPS.
    return RemoteProcessingClassification.cra_art_3_2_in_scope


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

    def assess_element(
        self,
        element_id: UUID,
        payload: RemoteProcessingAssessRequest,
        actor: object,
    ) -> RemoteProcessingElementRead:
        """Apply the CRA Art. 3(2) decision tree and persist the classification."""
        element = self.repository.get_or_404(element_id)

        element.is_developed_by_manufacturer    = payload.is_developed_by_manufacturer
        element.is_necessary_for_product_function = payload.is_necessary_for_product_function
        element.directly_interacts_with_product = payload.directly_interacts_with_product
        element.has_bidirectional_exchange      = payload.has_bidirectional_exchange
        element.provider_is_nis2_msp            = payload.provider_is_nis2_msp
        element.classification_rationale        = payload.classification_rationale
        element.classification                  = _classify(payload)
        element.assessed_at                     = datetime.now(UTC)
        element.assessed_by_user_id             = getattr(actor, "id", None)

        self.db.flush()
        create_audit_event(
            self.db,
            actor_user_id=getattr(actor, "id", None),
            action_type=AuditActionType.update,
            entity_type=EntityType.remote_processing_element,
            entity_id=element.id,
            status=AuditStatus.success,
            details_json={
                "action": "cra_assessment",
                "classification": element.classification,
                "is_developed_by_manufacturer": element.is_developed_by_manufacturer,
                "is_necessary_for_product_function": element.is_necessary_for_product_function,
                "directly_interacts_with_product": element.directly_interacts_with_product,
                "has_bidirectional_exchange": element.has_bidirectional_exchange,
            },
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