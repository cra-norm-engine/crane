from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_permissions_dependency
from app.core.database import get_db
from app.core.permissions import Permission
from app.models.enums import CertificationStatus, EvidenceType
from app.models.user import User
from app.schemas.artifact import ArtifactCreateLinkRevisionRequest
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


# ---------------------------------------------------------------------------
# Evidence attachment endpoints
# ---------------------------------------------------------------------------


@router.post("/{record_id}/evidence", response_model=CertificationRecordRead)
def attach_artifact_to_certification(
    record_id: UUID,
    payload: ArtifactCreateLinkRevisionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.certification_record_write)),
) -> CertificationRecordRead:
    return CertificationRecordService(db).attach_revision(
        record_id,
        payload.artifact_revision_id,
        actor_user_id=current_user.id,
    )


@router.post("/{record_id}/evidence/upload", response_model=CertificationRecordRead)
async def upload_evidence_for_certification(
    record_id: UUID,
    title: str = Form(...),
    artifact_type: EvidenceType = Form(...),
    description: str | None = Form(default=None),
    change_summary: str | None = Form(default=None),
    upload: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.certification_record_write)),
) -> CertificationRecordRead:
    return CertificationRecordRead.model_validate(
        await CertificationRecordService(db).upload_and_attach_evidence(
            record_id,
            actor_user_id=current_user.id,
            title=title,
            artifact_type=artifact_type,
            upload=upload,
            description=description,
            change_summary=change_summary,
        )
    )


@router.delete("/{record_id}/evidence/{link_id}", response_model=CertificationRecordRead)
def detach_evidence_from_certification(
    record_id: UUID,
    link_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.certification_record_write)),
) -> CertificationRecordRead:
    return CertificationRecordService(db).detach_revision(
        record_id,
        link_id,
        actor_user_id=current_user.id,
    )
