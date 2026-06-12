# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

import logging
from datetime import date, datetime
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import NotFoundException
from app.models.support_period_record import SupportPeriodNotificationRecipient, SupportPeriodRecord
from app.repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class SupportPeriodRecordRepository(BaseRepository[SupportPeriodRecord]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, SupportPeriodRecord)

    def _default_options(self):
        from app.models.user import User as UserModel
        return (
            selectinload(SupportPeriodRecord.product),
            selectinload(SupportPeriodRecord.notification_recipients).selectinload(
                SupportPeriodNotificationRecipient.user
            ),
            selectinload(SupportPeriodRecord.created_by_user),
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

    def get_active_by_product_id(
        self,
        product_id: UUID,
        product_release_id: UUID | None = None,
    ) -> SupportPeriodRecord | None:
        statement = (
            select(SupportPeriodRecord)
            .where(
                SupportPeriodRecord.product_id == product_id,
                SupportPeriodRecord.is_active.is_(True),
                SupportPeriodRecord.product_release_id == product_release_id,
            )
            .options(*self._default_options())
            .order_by(SupportPeriodRecord.created_at.desc())
        )
        return self.db.scalar(statement)

    def get_active_by_latest_release_for_product(
        self,
        product_id: UUID,
    ) -> SupportPeriodRecord | None:
        """Return the active support period for the product's latest release.

        Steps:
        1. Find the release with the highest system_version for the product.
        2. Return its active release-specific support period (product_release_id = that ID).
        3. If no release-specific record exists (or there are no releases at all),
           fall back to the product-level record (product_release_id IS NULL).  This
           ensures backward compatibility with data that was created before per-release
           support periods were introduced.
        """
        from app.models.product import ProductRelease

        # Step 1: resolve the latest release ID with an explicit scalar query so the
        # result is clear and logged, rather than buried inside a correlated subquery.
        latest_release_id: UUID | None = self.db.scalar(
            select(ProductRelease.id)
            .where(ProductRelease.product_id == product_id)
            .order_by(ProductRelease.system_version.desc())
            .limit(1)
        )
        logger.debug(
            "get_active_by_latest_release_for_product: product_id=%s latest_release_id=%s",
            product_id,
            latest_release_id,
        )

        # Step 2: look for a release-specific active record.
        if latest_release_id is not None:
            record = self.db.scalar(
                select(SupportPeriodRecord)
                .where(
                    SupportPeriodRecord.product_id == product_id,
                    SupportPeriodRecord.is_active.is_(True),
                    SupportPeriodRecord.product_release_id == latest_release_id,
                )
                .options(*self._default_options())
                .order_by(SupportPeriodRecord.created_at.desc())
            )
            if record is not None:
                logger.debug(
                    "get_active_by_latest_release_for_product: found release-specific record id=%s",
                    record.id,
                )
                return record

        # Step 3: fall back to the product-level active record (NULL product_release_id).
        # This covers two cases: (a) no releases exist yet, (b) the latest release has no
        # release-specific SP but there is a product-level one from before per-release SPs
        # were introduced.
        fallback = self.get_active_by_product_id(product_id, product_release_id=None)
        logger.debug(
            "get_active_by_latest_release_for_product: fallback product-level record id=%s",
            getattr(fallback, "id", None),
        )
        return fallback

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
