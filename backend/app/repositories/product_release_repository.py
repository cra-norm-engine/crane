from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.models.product import ProductRelease
from app.repositories.base import BaseRepository


class ProductReleaseRepository(BaseRepository[ProductRelease]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, ProductRelease)

    def list_all(self, *, product_id: UUID | None = None) -> list[ProductRelease]:
        statement = select(ProductRelease).order_by(ProductRelease.created_at.desc())
        if product_id:
            statement = statement.where(ProductRelease.product_id == product_id)
        return list(self.db.scalars(statement).all())

    def get_or_404(self, release_id: UUID) -> ProductRelease:
        release = self.get_by_id(release_id)
        if release is None:
            raise NotFoundException("Product release not found")
        return release

    def get_by_product_and_version(self, *, product_id: UUID, version: str) -> ProductRelease | None:
        statement = select(ProductRelease).where(
            ProductRelease.product_id == product_id,
            ProductRelease.version == version,
        )
        return self.db.scalar(statement)