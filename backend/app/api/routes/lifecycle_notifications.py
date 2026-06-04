from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import require_permissions_dependency
from app.core.database import get_db
from app.core.permissions import Permission
from app.models.enums import LifecycleNotificationStatus, LifecycleNotificationType
from app.models.user import User
from app.schemas.lifecycle_notification import (
    LifecycleNotificationDismissRequest,
    LifecycleNotificationMarkSentRequest,
    LifecycleNotificationRead,
)
from app.services.lifecycle_notification_service import LifecycleNotificationService

router = APIRouter()


@router.get("/", response_model=list[LifecycleNotificationRead])
def list_lifecycle_notifications(
    status: LifecycleNotificationStatus | None = Query(default=None),
    support_period_record_id: UUID | None = Query(default=None),
    notification_type: LifecycleNotificationType | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.lifecycle_notification_read)),
) -> list[LifecycleNotificationRead]:
    return LifecycleNotificationService(db).list_notifications(
        status=status,
        support_period_record_id=support_period_record_id,
        notification_type=notification_type,
        recipient_user_id=current_user.id,
    )


@router.get("/{notification_id}", response_model=LifecycleNotificationRead)
def get_lifecycle_notification(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.lifecycle_notification_read)),
) -> LifecycleNotificationRead:
    return LifecycleNotificationService(db).get_notification(notification_id)


@router.post("/schedule-eos-check", response_model=list[LifecycleNotificationRead])
def schedule_end_of_support_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.lifecycle_notification_write)),
) -> list[LifecycleNotificationRead]:
    return LifecycleNotificationService(db).schedule_end_of_support_notifications(actor=current_user)


@router.post("/{notification_id}/mark-sent", response_model=LifecycleNotificationRead)
def mark_lifecycle_notification_sent(
    notification_id: UUID,
    payload: LifecycleNotificationMarkSentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.lifecycle_notification_write)),
) -> LifecycleNotificationRead:
    return LifecycleNotificationService(db).mark_notification_sent(
        notification_id,
        actor=current_user,
        sent_at=payload.sent_at,
    )


@router.post("/{notification_id}/dismiss", response_model=LifecycleNotificationRead)
def dismiss_lifecycle_notification(
    notification_id: UUID,
    payload: LifecycleNotificationDismissRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.lifecycle_notification_write)),
) -> LifecycleNotificationRead:
    return LifecycleNotificationService(db).dismiss_notification(
        notification_id,
        actor=current_user,
        dismissed_at=payload.dismissed_at,
    )