# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

from __future__ import annotations

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Query, Response, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.permissions import Permission, require_permissions
from app.models.enums import EvidenceType
from app.models.user import User
from app.schemas.artifact import (
    ArtifactListRead,
    ArtifactRead,
    IntegritySweepResult,
    LegalHoldRequest,
)
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
    # NotFoundException etc. are converted to the canonical error shape by the
    # global exception handlers — no manual HTTPException translation needed.
    require_permissions(current_user, {Permission.evidence_item_write})
    service = ArtifactService(db)
    return ArtifactRead.model_validate(
        await service.upload_revision(
            artifact_id,
            uploaded_by_user_id=current_user.id,
            upload=upload,
            change_summary=change_summary,
            product_id=product_id,
        )
    )


@router.post("/{artifact_id}/snapshot", response_model=ArtifactRead)
async def snapshot_external_artifact(
    artifact_id: UUID,
    change_summary: str | None = Form(default=None),
    product_id: UUID | None = Form(default=None),
    upload: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ArtifactRead:
    """
    Store a retained copy of an externally-linked document as a new uploaded
    revision, so CRANE holds a hashed, retained snapshot rather than only a URL.
    """
    require_permissions(current_user, {Permission.evidence_item_write})
    service = ArtifactService(db)
    return ArtifactRead.model_validate(
        await service.upload_revision(
            artifact_id,
            uploaded_by_user_id=current_user.id,
            upload=upload,
            change_summary=change_summary or "Snapshot of external document",
            product_id=product_id,
        )
    )


@router.post("/verify-integrity", response_model=IntegritySweepResult)
def verify_artifacts_integrity(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IntegritySweepResult:
    """
    Re-hash every stored file and flag any that no longer match their recorded
    SHA-256 (tamper / corruption). Intended for manual or scheduled (cron) runs.
    """
    require_permissions(current_user, {Permission.evidence_item_write})
    service = ArtifactService(db)
    return IntegritySweepResult.model_validate(service.verify_all(actor_user_id=current_user.id))


@router.patch("/{artifact_id}/legal-hold", response_model=ArtifactRead)
def set_artifact_legal_hold(
    artifact_id: UUID,
    payload: LegalHoldRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ArtifactRead:
    require_permissions(current_user, {Permission.artifact_legal_hold})
    service = ArtifactService(db)
    return ArtifactRead.model_validate(
        service.set_legal_hold(
            artifact_id, hold=payload.hold, reason=payload.reason, actor_user_id=current_user.id
        )
    )


@router.delete("/{artifact_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_artifact(
    artifact_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Permanently delete an artifact + files — refused under retention/legal hold."""
    require_permissions(current_user, {Permission.artifact_delete})
    ArtifactService(db).delete_artifact(artifact_id, actor_user_id=current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/revisions/{revision_id}/download")
def download_artifact_revision(
    revision_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Integrity is re-verified before streaming; a tampered/corrupted file is
    # blocked (409) and audited. See ArtifactService.get_revision_for_download.
    require_permissions(current_user, {Permission.evidence_item_read})
    service = ArtifactService(db)
    revision = service.get_revision_for_download(revision_id, actor_user_id=current_user.id)
    path = Path(revision.storage_path)  # guaranteed present by the service
    return FileResponse(path, filename=revision.original_filename or path.name, media_type=revision.content_type)
