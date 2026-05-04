from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import require_permissions_dependency
from app.core.database import get_db
from app.core.permissions import Permission
from app.models.user import User
from app.schemas.sbom_record import SbomRecordCreate, SbomRecordRead, SbomRecordUpdate
from app.services.sbom_record_service import SbomRecordService

router = APIRouter()


@router.get("/", response_model=list[SbomRecordRead])
def list_sbom_records(
    product_release_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.security_update_read)),
) -> list[SbomRecordRead]:
    return SbomRecordService(db).list_sbom_records(product_release_id=product_release_id)


@router.post("/", response_model=SbomRecordRead, status_code=status.HTTP_201_CREATED)
def create_sbom_record(
    payload: SbomRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.security_update_write)),
) -> SbomRecordRead:
    return SbomRecordService(db).create_sbom_record(payload, actor=current_user)


@router.get("/{sbom_id}", response_model=SbomRecordRead)
def get_sbom_record(
    sbom_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.security_update_read)),
) -> SbomRecordRead:
    return SbomRecordService(db).get_sbom_record(sbom_id)


@router.put("/{sbom_id}", response_model=SbomRecordRead)
def update_sbom_record(
    sbom_id: UUID,
    payload: SbomRecordUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.security_update_write)),
) -> SbomRecordRead:
    return SbomRecordService(db).update_sbom_record(sbom_id, payload, actor=current_user)


@router.delete("/{sbom_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_sbom_record(
    sbom_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.security_update_write)),
) -> Response:
    SbomRecordService(db).delete_sbom_record(sbom_id, actor=current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
