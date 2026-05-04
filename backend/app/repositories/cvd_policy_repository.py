from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.models.cvd_policy import CvdPolicy
from app.repositories.base import BaseRepository


class CvdPolicyRepository(BaseRepository[CvdPolicy]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, CvdPolicy)

    def list_all(self, *, product_id: UUID | None = None) -> list[CvdPolicy]:
        statement = select(CvdPolicy).order_by(CvdPolicy.created_at.desc())
        if product_id:
            statement = statement.where(CvdPolicy.product_id == product_id)
        return list(self.db.scalars(statement).all())

    def get_or_404(self, cvd_policy_id: UUID) -> CvdPolicy:
        policy = self.get_by_id(cvd_policy_id)
        if policy is None:
            raise NotFoundException("CVD policy not found")
        return policy
