from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import NotFoundException
from app.models.lifecycle_notification import LifecycleNotification
from app.models.enums import LifecycleNotificationStatus, LifecycleNotificationType
from app.repositories.base import BaseRepository


class LifecycleNotificationRepository(BaseRepository[LifecycleNotification]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, LifecycleNotification)

    def _default_options(self):
        return (
            selectinload(LifecycleNotification.recipient_user),
            selectinload(LifecycleNotification.support_period_record),
        )

    def list_all(
        self,
        *,
        status: LifecycleNotificationStatus | None = None,
        notification_type: LifecycleNotificationType | None = None,
        support_period_record_id: UUID | None = None,
    ) -> list[LifecycleNotification]:
        statement = (
            select(LifecycleNotification)
            .options(*self._default_options())
            .order_by(LifecycleNotification.created_at.desc())
        )

        if status is not None:
            statement = statement.where(LifecycleNotification.status == status)

        if notification_type is not None:
            statement = statement.where(LifecycleNotification.notification_type == notification_type)

        if support_period_record_id is not None:
            statement = statement.where(
                LifecycleNotification.support_period_record_id == support_period_record_id
            )

        return list(self.db.scalars(statement).all())

    def get_or_404(self, notification_id: UUID) -> LifecycleNotification:
        notification = self.get_by_id(notification_id)
        if notification is None:
            raise NotFoundException("Lifecycle notification not found")
        return notification

    def get_by_record_and_type(
        self,
        *,
        support_period_record_id: UUID,
        notification_type: LifecycleNotificationType,
        recipient_user_id: UUID | None,
    ) -> LifecycleNotification | None:
        statement = (
            select(LifecycleNotification)
            .options(*self._default_options())
            .where(
                LifecycleNotification.support_period_record_id == support_period_record_id,
                LifecycleNotification.notification_type == notification_type,
                LifecycleNotification.recipient_user_id == recipient_user_id,
            )
        )
        return self.db.scalar(statement)

    def get_by_security_update_and_type(
        self,
        *,
        security_update_id: UUID,
        notification_type: LifecycleNotificationType,
        recipient_user_id: UUID | None,
    ) -> LifecycleNotification | None:
        statement = (
            select(LifecycleNotification)
            .options(*self._default_options())
            .where(
                LifecycleNotification.security_update_id == security_update_id,
                LifecycleNotification.notification_type == notification_type,
                LifecycleNotification.recipient_user_id == recipient_user_id,
            )
        )
        return self.db.scalar(statement)

    def list_pending_due(self, now: datetime) -> list[LifecycleNotification]:
        statement = (
            select(LifecycleNotification)
            .options(*self._default_options())
            .where(
                LifecycleNotification.status == LifecycleNotificationStatus.pending,
                LifecycleNotification.scheduled_for <= now,
            )
            .order_by(LifecycleNotification.scheduled_for.asc(), LifecycleNotification.created_at.asc())
        )
        return list(self.db.scalars(statement).all())
