from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import create_audit_event
from app.core.exceptions import ConflictException
from app.models.enums import (
    AuditActionType,
    AuditStatus,
    EntityType,
    LifecycleNotificationStatus,
    LifecycleNotificationType,
)
from app.models.lifecycle_notification import LifecycleNotification
from app.repositories.lifecycle_notification_repository import LifecycleNotificationRepository
from app.repositories.support_period_record_repository import SupportPeriodRecordRepository
from app.schemas.lifecycle_notification import LifecycleNotificationRead


class LifecycleNotificationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = LifecycleNotificationRepository(db)
        self.support_period_repository = SupportPeriodRecordRepository(db)

    def list_notifications(
        self,
        *,
        status: LifecycleNotificationStatus | None = None,
        support_period_record_id: UUID | None = None,
    ) -> list[LifecycleNotificationRead]:
        notifications = self.repository.list_all(
            status=status,
            support_period_record_id=support_period_record_id,
        )
        return [LifecycleNotificationRead.model_validate(item) for item in notifications]

    def get_notification(self, notification_id: UUID) -> LifecycleNotificationRead:
        notification = self.repository.get_or_404(notification_id)
        return LifecycleNotificationRead.model_validate(notification)

    def schedule_end_of_support_notifications(
        self,
        *,
        actor: object | None = None,
        today: date | None = None,
    ) -> list[LifecycleNotificationRead]:
        effective_today = today or datetime.now(UTC).date()
        notify_on_or_after = effective_today + timedelta(days=183)

        records = self.support_period_repository.list_due_for_eos_notification(
            today=effective_today,
            notify_on_or_after=notify_on_or_after,
        )

        created_notifications: list[LifecycleNotification] = []

        for record in records:
            existing = self.repository.get_by_record_and_type(
                support_period_record_id=record.id,
                notification_type=LifecycleNotificationType.end_of_support_upcoming,
            )
            if existing is not None:
                continue

            scheduled_for = datetime.combine(effective_today, time.min, tzinfo=UTC)
            notification = LifecycleNotification(
                support_period_record_id=record.id,
                notification_type=LifecycleNotificationType.end_of_support_upcoming,
                status=LifecycleNotificationStatus.pending,
                scheduled_for=scheduled_for,
                title="End of support approaching",
                message=(
                    f"Product support ends on {record.support_end_date.isoformat()} for product "
                    f"{record.product_id}. Review user-facing communication and lifecycle planning."
                ),
            )

            try:
                self.repository.add(notification)
                created_notifications.append(notification)

                create_audit_event(
                    self.db,
                    actor_user_id=getattr(actor, "id", None) if actor is not None else None,
                    action_type=AuditActionType.notify,
                    entity_type=EntityType.lifecycle_notification,
                    entity_id=notification.id,
                    status=AuditStatus.success,
                    details_json={
                        "support_period_record_id": str(record.id),
                        "product_id": str(record.product_id),
                        "notification_type": notification.notification_type.value,
                        "scheduled_for": notification.scheduled_for.isoformat(),
                    },
                )
            except IntegrityError:
                self.db.rollback()
                continue

        if created_notifications:
            self.db.commit()
            for notification in created_notifications:
                self.db.refresh(notification)

        return [LifecycleNotificationRead.model_validate(item) for item in created_notifications]

    def mark_notification_sent(
        self,
        notification_id: UUID,
        *,
        actor: object,
        sent_at: datetime | None = None,
    ) -> LifecycleNotificationRead:
        notification = self.repository.get_or_404(notification_id)
        notification.status = LifecycleNotificationStatus.sent
        notification.sent_at = sent_at or datetime.now(UTC)

        support_period_record = self.support_period_repository.get_or_404(notification.support_period_record_id)
        if support_period_record.eos_notification_sent_at is None:
            support_period_record.eos_notification_sent_at = notification.sent_at

        self.db.flush()
        create_audit_event(
            self.db,
            actor_user_id=getattr(actor, "id", None),
            action_type=AuditActionType.update,
            entity_type=EntityType.lifecycle_notification,
            entity_id=notification.id,
            status=AuditStatus.success,
            details_json={
                "status": notification.status.value,
                "sent_at": notification.sent_at.isoformat() if notification.sent_at else None,
            },
        )
        self.db.commit()
        self.db.refresh(notification)
        return LifecycleNotificationRead.model_validate(notification)

    def dismiss_notification(
        self,
        notification_id: UUID,
        *,
        actor: object,
        dismissed_at: datetime | None = None,
    ) -> LifecycleNotificationRead:
        notification = self.repository.get_or_404(notification_id)
        notification.status = LifecycleNotificationStatus.dismissed
        notification.dismissed_at = dismissed_at or datetime.now(UTC)

        self.db.flush()
        create_audit_event(
            self.db,
            actor_user_id=getattr(actor, "id", None),
            action_type=AuditActionType.update,
            entity_type=EntityType.lifecycle_notification,
            entity_id=notification.id,
            status=AuditStatus.success,
            details_json={
                "status": notification.status.value,
                "dismissed_at": notification.dismissed_at.isoformat() if notification.dismissed_at else None,
            },
        )
        self.db.commit()
        self.db.refresh(notification)
        return LifecycleNotificationRead.model_validate(notification)