from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_permissions_dependency
from app.core.database import get_db
from app.core.permissions import Permission
from app.models.user import User
from app.schemas.support_period_record import (
    SupportPeriodRecordCreate,
    SupportPeriodRecordHistoryRead,
    SupportPeriodNotificationRecipientOptionRead,
    SupportPeriodRecordRead,
    SupportPeriodRecordUpdate,
    SupportPeriodSnippetGenerateRequest,
    SupportPeriodSnippetRead,
)
from app.services.support_period_record_service import SupportPeriodRecordService

router = APIRouter()


@router.get("/notification-recipients", response_model=list[SupportPeriodNotificationRecipientOptionRead])
def list_support_period_notification_recipients(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.support_period_read)),
) -> list[SupportPeriodNotificationRecipientOptionRead]:
    return SupportPeriodRecordService(db).list_notification_recipient_options()


@router.get("/", response_model=list[SupportPeriodRecordRead])
def list_support_period_records(
    product_id: UUID | None = Query(default=None),
    active_only: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.support_period_read)),
) -> list[SupportPeriodRecordRead]:
    return SupportPeriodRecordService(db).list_records(
        product_id=product_id,
        active_only=active_only,
    )


@router.post("/", response_model=SupportPeriodRecordRead, status_code=status.HTTP_201_CREATED)
def create_support_period_record(
    payload: SupportPeriodRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.support_period_write)),
) -> SupportPeriodRecordRead:
    return SupportPeriodRecordService(db).create_record(payload, actor=current_user)


@router.post("/generate-snippets", response_model=SupportPeriodSnippetRead)
def generate_support_period_snippets(
    payload: SupportPeriodSnippetGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.support_period_read)),
) -> SupportPeriodSnippetRead:
    return SupportPeriodRecordService(db).generate_snippets(payload)


@router.get("/product/{product_id}/active", response_model=SupportPeriodRecordRead)
def get_active_support_period_record_for_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.support_period_read)),
) -> SupportPeriodRecordRead:
    return SupportPeriodRecordService(db).get_active_record_for_product(product_id)


@router.get("/product/{product_id}/history", response_model=SupportPeriodRecordHistoryRead)
def get_support_period_history_for_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.support_period_read)),
) -> SupportPeriodRecordHistoryRead:
    return SupportPeriodRecordService(db).get_history_for_product(product_id)


@router.get("/{record_id}", response_model=SupportPeriodRecordRead)
def get_support_period_record(
    record_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.support_period_read)),
) -> SupportPeriodRecordRead:
    return SupportPeriodRecordService(db).get_record(record_id)


@router.put("/{record_id}", response_model=SupportPeriodRecordRead)
def update_support_period_record(
    record_id: UUID,
    payload: SupportPeriodRecordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.support_period_write)),
) -> SupportPeriodRecordRead:
    return SupportPeriodRecordService(db).update_record_versioned(
        record_id,
        payload,
        actor=current_user,
    )
