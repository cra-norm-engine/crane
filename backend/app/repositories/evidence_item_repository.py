from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.models.evidence_item import EvidenceItem
from app.repositories.base import BaseRepository


class EvidenceItemRepository(BaseRepository[EvidenceItem]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, EvidenceItem)

    def list_by_risk_assessment(self, risk_assessment_id: UUID) -> list[EvidenceItem]:
        stmt = (
            select(EvidenceItem)
            .where(EvidenceItem.risk_assessment_id == risk_assessment_id)
            .order_by(EvidenceItem.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def list_by_requirement_mapping(self, requirement_mapping_id: UUID) -> list[EvidenceItem]:
        stmt = (
            select(EvidenceItem)
            .where(EvidenceItem.requirement_mapping_id == requirement_mapping_id)
            .order_by(EvidenceItem.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def list_by_product_release(self, product_release_id: UUID) -> list[EvidenceItem]:
        stmt = (
            select(EvidenceItem)
            .where(EvidenceItem.product_release_id == product_release_id)
            .order_by(EvidenceItem.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def get_or_404(self, evidence_item_id: UUID) -> EvidenceItem:
        evidence_item = self.get_by_id(evidence_item_id)
        if evidence_item is None:
            raise NotFoundException("Evidence item not found")
        return evidence_item