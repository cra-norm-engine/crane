from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.exceptions import NotFoundException
from app.models.product import ProductRelease
from app.models.sbom_record import SbomRecord
from app.repositories.base import BaseRepository


class SbomRecordRepository(BaseRepository[SbomRecord]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, SbomRecord)

    def list_all(
        self,
        *,
        product_release_id: UUID | None = None,
        product_id: UUID | None = None,
    ) -> list[SbomRecord]:
        statement = select(SbomRecord).order_by(SbomRecord.created_at.desc())
        if product_release_id:
            statement = statement.where(SbomRecord.product_release_id == product_release_id)
        elif product_id:
            # Filter by all releases that belong to this product.
            statement = statement.join(
                ProductRelease,
                SbomRecord.product_release_id == ProductRelease.id,
            ).where(ProductRelease.product_id == product_id)
        return list(self.db.scalars(statement).all())

    def get_or_404(self, sbom_record_id: UUID) -> SbomRecord:
        record = self.get_by_id(sbom_record_id)
        if record is None:
            raise NotFoundException("SBOM record not found")
        return record
