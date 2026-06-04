from __future__ import annotations

import logging
from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import create_audit_event
from app.core.exceptions import ConflictException, NotFoundException
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

logger = logging.getLogger(__name__)


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
        notification_type: LifecycleNotificationType | None = None,
        recipient_user_id: UUID | None = None,
    ) -> list[LifecycleNotificationRead]:
        notifications = self.repository.list_all(
            status=status,
            support_period_record_id=support_period_record_id,
            notification_type=notification_type,
            recipient_user_id=recipient_user_id,
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
        records = self.support_period_repository.list_all(active_only=True)

        created_notifications: list[LifecycleNotification] = []

        for record in records:
            if record.eos_notification_sent_at is not None:
                continue

            if not record.notification_recipients:
                continue

            scheduled_date = record.support_end_date - timedelta(days=record.notify_before_days)
            if scheduled_date > effective_today:
                continue

            scheduled_for = datetime.combine(scheduled_date, time.min, tzinfo=UTC)

            for recipient in record.notification_recipients:
                existing = self.repository.get_by_record_and_type(
                    support_period_record_id=record.id,
                    notification_type=LifecycleNotificationType.end_of_support_upcoming,
                    recipient_user_id=recipient.user_id,
                )
                if existing is not None:
                    continue

                product_name = getattr(record.product, "name", "this product")
                notification = LifecycleNotification(
                    support_period_record_id=record.id,
                    security_update_id=None,
                    recipient_user_id=recipient.user_id,
                    notification_type=LifecycleNotificationType.end_of_support_upcoming,
                    status=LifecycleNotificationStatus.pending,
                    scheduled_for=scheduled_for,
                    title="End of support approaching",
                    message=(
                        f"{product_name} reaches end of support on {record.support_end_date.isoformat()}. "
                        f"Review lifecycle communication and support planning."
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
                            "recipient_user_id": str(recipient.user_id),
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

    def create_security_update_notifications(
        self,
        security_update_id: UUID,
        actor: object | None = None,
    ) -> list[LifecycleNotificationRead]:
        """
        Create pending notifications for each recipient on the product's active support
        period when a new security update is published (CRA Annex I Part II §8).
        """
        from app.models.security_update import SecurityUpdate
        from app.models.support_period_record import SupportPeriodRecord

        su = self.db.get(SecurityUpdate, security_update_id)
        if su is None:
            raise NotFoundException(f"SecurityUpdate {security_update_id} not found")

        release = su.product_release
        product = release.product

        # Use the product's active support period to resolve recipients.
        active_record = (
            self.db.query(SupportPeriodRecord)
            .filter_by(product_id=product.id, is_active=True)
            .first()
        )

        # Collect recipients — fall back to the actor if no support period or no recipients.
        if active_record and active_record.notification_recipients:
            recipient_user_ids = [r.user_id for r in active_record.notification_recipients]
        elif actor is not None and hasattr(actor, "id"):
            recipient_user_ids = [actor.id]
        else:
            logger.debug(
                "No recipients and no actor for product %s — skipping security update notifications",
                product.id,
            )
            return []

        severity_label = su.severity.value.upper() if su.severity else "UNRATED"
        cves = (
            ", ".join(str(c) for c in su.cves_addressed_json)
            if su.cves_addressed_json
            else "No CVEs listed"
        )
        created: list[LifecycleNotification] = []

        support_record_id = active_record.id if active_record else None

        for user_id in recipient_user_ids:
            existing = self.repository.get_by_security_update_and_type(
                security_update_id=su.id,
                notification_type=LifecycleNotificationType.security_update_available,
                recipient_user_id=user_id,
            )
            if existing is not None:
                continue

            notif = LifecycleNotification(
                support_period_record_id=support_record_id,
                security_update_id=su.id,
                recipient_user_id=user_id,
                notification_type=LifecycleNotificationType.security_update_available,
                status=LifecycleNotificationStatus.pending,
                scheduled_for=datetime.now(UTC),
                title=f"Security update available — {product.name} v{release.system_version}",
                message=(
                    f"A {severity_label} security update '{su.title}' is available for "
                    f"{product.name} v{release.system_version}. CVEs: {cves}."
                ),
            )
            self.db.add(notif)
            created.append(notif)

        if created:
            self.db.flush()
            for notif in created:
                create_audit_event(
                    self.db,
                    actor_user_id=getattr(actor, "id", None) if actor is not None else None,
                    action_type=AuditActionType.notify,
                    entity_type=EntityType.lifecycle_notification,
                    entity_id=notif.id,
                    status=AuditStatus.success,
                    details_json={
                        "security_update_id": str(su.id),
                        "product_id": str(product.id),
                        "product_release_id": str(release.id),
                        "recipient_user_id": str(recipient.user_id),
                        "notification_type": notif.notification_type.value,
                    },
                )
            self.db.commit()
            for notif in created:
                self.db.refresh(notif)

        return [LifecycleNotificationRead.model_validate(n) for n in created]

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

        # Only update eos_notification_sent_at for EOS-type notifications.
        if notification.support_period_record_id is not None:
            support_period_record = self.support_period_repository.get_or_404(
                notification.support_period_record_id
            )
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
