from __future__ import annotations

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.exceptions import ConflictException, NotFoundException
from app.core.permissions import Permission, require_permissions
from app.models.enums import EvidenceType
from app.models.user import User
from app.schemas.artifact import ArtifactListRead, ArtifactRead
from app.services.artifact_service import ArtifactService

router = APIRouter()


@router.get("", response_model=list[ArtifactListRead])
def list_artifacts(
    product_id: UUID | None = Query(default=None),
    query: str | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ArtifactListRead]:
    require_permissions(current_user, {Permission.evidence_item_read})
    service = ArtifactService(db)
    return [ArtifactListRead.model_validate(item) for item in service.list(product_id=product_id, query=query)]


@router.get("/{artifact_id}", response_model=ArtifactRead)
def get_artifact(
    artifact_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ArtifactRead:
    require_permissions(current_user, {Permission.evidence_item_read})
    service = ArtifactService(db)
    return ArtifactRead.model_validate(service.get(artifact_id))


@router.post("/upload", response_model=ArtifactRead, status_code=status.HTTP_201_CREATED)
async def create_uploaded_artifact(
    title: str = Form(...),
    artifact_type: EvidenceType = Form(...),
    description: str | None = Form(default=None),
    change_summary: str | None = Form(default=None),
    product_id: UUID | None = Form(default=None),
    upload: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ArtifactRead:
    require_permissions(current_user, {Permission.evidence_item_write})
    service = ArtifactService(db)
    return ArtifactRead.model_validate(
        await service.create_with_upload(
            title=title,
            artifact_type=artifact_type,
            created_by_user_id=current_user.id,
            upload=upload,
            description=description,
            change_summary=change_summary,
            product_id=product_id,
        )
    )


@router.post("/external-link", response_model=ArtifactRead, status_code=status.HTTP_201_CREATED)
def create_external_link_artifact(
    title: str = Form(...),
    artifact_type: EvidenceType = Form(...),
    external_url: str = Form(...),
    description: str | None = Form(default=None),
    change_summary: str | None = Form(default=None),
    product_id: UUID | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ArtifactRead:
    require_permissions(current_user, {Permission.evidence_item_write})
    service = ArtifactService(db)
    return ArtifactRead.model_validate(
        service.create_external_link(
            title=title,
            artifact_type=artifact_type,
            created_by_user_id=current_user.id,
            external_url=external_url,
            description=description,
            change_summary=change_summary,
            product_id=product_id,
        )
    )


@router.post("/{artifact_id}/revisions/upload", response_model=ArtifactRead)
async def upload_artifact_revision(
    artifact_id: UUID,
    change_summary: str | None = Form(default=None),
    product_id: UUID | None = Form(default=None),
    upload: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ArtifactRead:
    require_permissions(current_user, {Permission.evidence_item_write})
    service = ArtifactService(db)
    try:
        return ArtifactRead.model_validate(
            await service.upload_revision(
                artifact_id,
                uploaded_by_user_id=current_user.id,
                upload=upload,
                change_summary=change_summary,
                product_id=product_id,
            )
        )
    except NotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/revisions/{revision_id}/download")
def download_artifact_revision(
    revision_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_permissions(current_user, {Permission.evidence_item_read})
    service = ArtifactService(db)
    revision = service.artifact_revision_repository.get_or_404(revision_id)
    if not revision.storage_path:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="External link revisions cannot be downloaded.")
    path = Path(revision.storage_path)
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Stored artifact file not found.")
    return FileResponse(path, filename=revision.original_filename or path.name, media_type=revision.content_type)
