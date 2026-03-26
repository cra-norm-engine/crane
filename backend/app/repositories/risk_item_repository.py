from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import NotFoundException
from app.models.risk_item import RiskItem
from app.repositories.base import BaseRepository


class RiskItemRepository(BaseRepository[RiskItem]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, RiskItem)

    def list_by_assessment(self, risk_assessment_id: UUID) -> list[RiskItem]:
        stmt = (
            select(RiskItem)
            .where(RiskItem.risk_assessment_id == risk_assessment_id)
            .order_by(RiskItem.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def get_with_relations(self, risk_item_id: UUID) -> RiskItem | None:
        stmt = (
            select(RiskItem)
            .where(RiskItem.id == risk_item_id)
            .options(
                selectinload(RiskItem.requirement_mappings),
            )
        )
        return self.db.scalar(stmt)

    def get_or_404(self, risk_item_id: UUID) -> RiskItem:
        risk_item = self.get_by_id(risk_item_id)
        if risk_item is None:
            raise NotFoundException("Risk item not found")
        return risk_item