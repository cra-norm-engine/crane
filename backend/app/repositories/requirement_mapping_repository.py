from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import NotFoundException
from app.models.requirement_mapping import RequirementMapping
from app.repositories.base import BaseRepository


class RequirementMappingRepository(BaseRepository[RequirementMapping]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, RequirementMapping)

    def list_by_risk_item(self, risk_item_id: UUID) -> list[RequirementMapping]:
        stmt = (
            select(RequirementMapping)
            .where(RequirementMapping.risk_item_id == risk_item_id)
            .order_by(RequirementMapping.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def list_by_annex_requirement(self, annex_requirement_id: UUID) -> list[RequirementMapping]:
        stmt = (
            select(RequirementMapping)
            .where(RequirementMapping.annex_requirement_id == annex_requirement_id)
            .order_by(RequirementMapping.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def list_for_matrix(self) -> list[RequirementMapping]:
        stmt = (
            select(RequirementMapping)
            .options(
                selectinload(RequirementMapping.annex_requirement),
                selectinload(RequirementMapping.risk_item),
                selectinload(RequirementMapping.evidence_items),
            )
            .order_by(RequirementMapping.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def get_with_relations(self, mapping_id: UUID) -> RequirementMapping | None:
        stmt = (
            select(RequirementMapping)
            .where(RequirementMapping.id == mapping_id)
            .options(
                selectinload(RequirementMapping.annex_requirement),
                selectinload(RequirementMapping.risk_item),
                selectinload(RequirementMapping.evidence_items),
            )
        )
        return self.db.scalar(stmt)

    def get_or_404(self, mapping_id: UUID) -> RequirementMapping:
        mapping = self.get_by_id(mapping_id)
        if mapping is None:
            raise NotFoundException("Requirement mapping not found")
        return mapping