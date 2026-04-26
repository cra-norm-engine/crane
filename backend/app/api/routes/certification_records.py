from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import require_permissions_dependency
from app.core.database import get_db
from app.core.permissions import Permission
from app.models.enums import CertificationStatus
from app.models.user import User
from app.schemas.certification_record import (
    CertificationRecordCreate,
    CertificationRecordRead,
    CertificationRecordUpdate,
)
from app.services.certification_record_service import CertificationRecordService

router = APIRouter()


@router.get("/", response_model=list[CertificationRecordRead])
def list_certification_records(
    product_id: UUID | None = Query(default=None),
    status: CertificationStatus | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.certification_record_read)),
) -> list[CertificationRecordRead]:
    return CertificationRecordService(db).list_records(product_id=product_id, status=status)


@router.post("/", response_model=CertificationRecordRead, status_code=status.HTTP_201_CREATED)
def create_certification_record(
    payload: CertificationRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.certification_record_write)),
) -> CertificationRecordRead:
    return CertificationRecordService(db).create_record(payload, actor=current_user)


@router.get("/{record_id}", response_model=CertificationRecordRead)
def get_certification_record(
    record_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.certification_record_read)),
) -> CertificationRecordRead:
    return CertificationRecordService(db).get_record(record_id)


@router.patch("/{record_id}", response_model=CertificationRecordRead)
def update_certification_record(
    record_id: UUID,
    payload: CertificationRecordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.certification_record_write)),
) -> CertificationRecordRead:
    return CertificationRecordService(db).update_record(record_id, payload, actor=current_user)


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_certification_record(
    record_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.certification_record_write)),
) -> Response:
    CertificationRecordService(db).delete_record(record_id, actor=current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
