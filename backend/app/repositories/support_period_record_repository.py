from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import NotFoundException
from app.models.support_period_record import SupportPeriodNotificationRecipient, SupportPeriodRecord
from app.repositories.base import BaseRepository


class SupportPeriodRecordRepository(BaseRepository[SupportPeriodRecord]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, SupportPeriodRecord)

    def _default_options(self):
        return (
            selectinload(SupportPeriodRecord.product),
            selectinload(SupportPeriodRecord.notification_recipients).selectinload(
                SupportPeriodNotificationRecipient.user
            ),
        )

    def list_all(
        self,
        *,
        product_id: UUID | None = None,
        active_only: bool = False,
    ) -> list[SupportPeriodRecord]:
        statement = (
            select(SupportPeriodRecord)
            .options(*self._default_options())
            .order_by(SupportPeriodRecord.created_at.desc())
        )

        if product_id:
            statement = statement.where(SupportPeriodRecord.product_id == product_id)

        if active_only:
            statement = statement.where(SupportPeriodRecord.is_active.is_(True))

        return list(self.db.scalars(statement).all())

    def get_or_404(self, record_id: UUID) -> SupportPeriodRecord:
        record = self.get_by_id(record_id)
        if record is None:
            raise NotFoundException("Support period record not found")
        return record

    def get_active_by_product_id(self, product_id: UUID) -> SupportPeriodRecord | None:
        statement = (
            select(SupportPeriodRecord)
            .where(
                SupportPeriodRecord.product_id == product_id,
                SupportPeriodRecord.is_active.is_(True),
            )
            .options(*self._default_options())
            .order_by(SupportPeriodRecord.created_at.desc())
        )
        return self.db.scalar(statement)

    def list_due_for_eos_notification(
        self,
        *,
        today: date,
        notify_on_or_after: date,
    ) -> list[SupportPeriodRecord]:
        statement = (
            select(SupportPeriodRecord)
            .where(
                SupportPeriodRecord.is_active.is_(True),
                SupportPeriodRecord.support_end_date >= today,
                SupportPeriodRecord.support_end_date <= notify_on_or_after,
                SupportPeriodRecord.eos_notification_sent_at.is_(None),
            )
            .options(*self._default_options())
            .order_by(SupportPeriodRecord.support_end_date.asc(), SupportPeriodRecord.created_at.desc())
        )
        return list(self.db.scalars(statement).all())

    def list_by_support_end_date_range(
        self,
        *,
        support_end_date_from: date | None = None,
        support_end_date_to: date | None = None,
        active_only: bool = False,
    ) -> list[SupportPeriodRecord]:
        statement = (
            select(SupportPeriodRecord)
            .options(*self._default_options())
            .order_by(
                SupportPeriodRecord.support_end_date.asc(),
                SupportPeriodRecord.created_at.desc(),
            )
        )

        conditions = []

        if support_end_date_from is not None:
            conditions.append(SupportPeriodRecord.support_end_date >= support_end_date_from)
        if support_end_date_to is not None:
            conditions.append(SupportPeriodRecord.support_end_date <= support_end_date_to)
        if active_only:
            conditions.append(SupportPeriodRecord.is_active.is_(True))

        if conditions:
            statement = statement.where(and_(*conditions))

        return list(self.db.scalars(statement).all())

    def list_current_or_historical_for_product(self, product_id: UUID) -> list[SupportPeriodRecord]:
        statement = (
            select(SupportPeriodRecord)
            .where(SupportPeriodRecord.product_id == product_id)
            .options(*self._default_options())
            .order_by(
                SupportPeriodRecord.is_active.desc(),
                SupportPeriodRecord.created_at.desc(),
            )
        )
        return list(self.db.scalars(statement).all())
