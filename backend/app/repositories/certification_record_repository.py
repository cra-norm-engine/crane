from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import NotFoundException
from app.models.certification_record import CertificationRecord
from app.models.enums import CertificationStatus
from app.repositories.base import BaseRepository


class CertificationRecordRepository(BaseRepository[CertificationRecord]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, CertificationRecord)

    def list_all(
        self,
        *,
        product_id: UUID | None = None,
        status: CertificationStatus | None = None,
    ) -> list[CertificationRecord]:
        statement = (
            select(CertificationRecord)
            .options(selectinload(CertificationRecord.product))
            .order_by(CertificationRecord.created_at.desc())
        )
        if product_id is not None:
            statement = statement.where(CertificationRecord.product_id == product_id)
        if status is not None:
            statement = statement.where(CertificationRecord.status == status)
        return list(self.db.scalars(statement).all())

    def get_or_404(self, record_id: UUID) -> CertificationRecord:
        record = self.db.scalar(
            select(CertificationRecord)
            .where(CertificationRecord.id == record_id)
            .options(selectinload(CertificationRecord.product))
        )
        if record is None:
            raise NotFoundException("Certification record not found")
        return record
