from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.product import ProductScopeEvaluation
from app.repositories.base import BaseRepository


class ProductScopeEvaluationRepository(BaseRepository[ProductScopeEvaluation]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, ProductScopeEvaluation)

    def list_for_product(self, product_id: UUID) -> list[ProductScopeEvaluation]:
        statement = (
            select(ProductScopeEvaluation)
            .where(ProductScopeEvaluation.product_id == product_id)
            .order_by(ProductScopeEvaluation.created_at.desc())
        )
        return list(self.db.scalars(statement).all())