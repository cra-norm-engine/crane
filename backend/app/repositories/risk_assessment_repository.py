from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import NotFoundException
from app.models.enums import RiskAssessmentStatus
from app.models.risk_assessment import RiskAssessment
from app.models.risk_item import RiskItem
from app.repositories.base import BaseRepository


class RiskAssessmentRepository(BaseRepository[RiskAssessment]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, RiskAssessment)

    def list_all(self) -> list[RiskAssessment]:
        stmt = select(RiskAssessment).order_by(RiskAssessment.created_at.desc())
        return list(self.db.scalars(stmt).all())

    def list_by_product(self, product_id: UUID) -> list[RiskAssessment]:
        stmt = (
            select(RiskAssessment)
            .where(RiskAssessment.product_id == product_id)
            .order_by(RiskAssessment.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def list_by_product_release(self, product_release_id: UUID) -> list[RiskAssessment]:
        stmt = (
            select(RiskAssessment)
            .where(RiskAssessment.product_release_id == product_release_id)
            .order_by(RiskAssessment.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def get_by_product_and_system_version(
        self,
        *,
        product_id: UUID,
        system_version: int,
    ) -> RiskAssessment | None:
        # Retrieve an assessment by product ID and system version (immutable version number)
        stmt = select(RiskAssessment).where(
            RiskAssessment.product_id == product_id,
            RiskAssessment.system_version == system_version,
        )
        return self.db.scalar(stmt)

    def get_with_relations(self, assessment_id: UUID) -> RiskAssessment | None:
        stmt = (
            select(RiskAssessment)
            .where(RiskAssessment.id == assessment_id)
            .options(
                selectinload(RiskAssessment.risk_items).selectinload(RiskItem.requirement_mappings),
                selectinload(RiskAssessment.evidence_items),
            )
        )
        return self.db.scalar(stmt)

    def get_or_404(self, assessment_id: UUID) -> RiskAssessment:
        assessment = self.get_by_id(assessment_id)
        if assessment is None:
            raise NotFoundException("Risk assessment not found")
        return assessment

