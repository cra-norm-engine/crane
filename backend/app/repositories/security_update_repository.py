from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.models.product import ProductRelease
from app.models.security_update import SecurityUpdate
from app.repositories.base import BaseRepository


class SecurityUpdateRepository(BaseRepository[SecurityUpdate]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, SecurityUpdate)

    def list_all(
        self,
        *,
        product_release_id: UUID | None = None,
        product_id: UUID | None = None,
    ) -> list[SecurityUpdate]:
        statement = select(SecurityUpdate).order_by(SecurityUpdate.created_at.desc())

        if product_release_id:
            statement = statement.where(SecurityUpdate.product_release_id == product_release_id)
        elif product_id:
            statement = statement.join(
                ProductRelease,
                SecurityUpdate.product_release_id == ProductRelease.id,
            ).where(ProductRelease.product_id == product_id)

        return list(self.db.scalars(statement).all())

    def get_or_404(self, security_update_id: UUID) -> SecurityUpdate:
        security_update = self.get_by_id(security_update_id)
        if security_update is None:
            raise NotFoundException("Security update not found")
        return security_update

    def list_by_release_ids(self, release_ids: list[UUID]) -> list[SecurityUpdate]:
        if not release_ids:
            return []

        statement = (
            select(SecurityUpdate)
            .where(SecurityUpdate.product_release_id.in_(release_ids))
            .order_by(SecurityUpdate.created_at.desc())
        )
        return list(self.db.scalars(statement).all())