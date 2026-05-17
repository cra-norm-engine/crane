from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.exceptions import ConflictException, NotFoundException
from app.core.permissions import Permission, require_permissions
from app.models.enums import EvidenceType
from app.models.user import User
from app.schemas.artifact import ArtifactCreateLinkRevisionRequest
from app.schemas.release_gate import GateItemCreateRequest, ReleaseGateDetailRead, ReleaseGateReviewRequest
from app.services.release_gate_service import ReleaseGateService

router = APIRouter()


@router.get("/product-releases/{product_release_id}/gate", response_model=ReleaseGateDetailRead)
def get_release_gate(
    product_release_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReleaseGateDetailRead:
    require_permissions(current_user, {Permission.release_read})
    service = ReleaseGateService(db)
    try:
        return ReleaseGateDetailRead.model_validate(service.get_or_create_by_release(product_release_id))
    except NotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/product-releases/{product_release_id}/gate/submit", response_model=ReleaseGateDetailRead)
def submit_release_gate(
    product_release_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReleaseGateDetailRead:
    require_permissions(current_user, {Permission.release_write})
    service = ReleaseGateService(db)
    try:
        return ReleaseGateDetailRead.model_validate(
            service.submit_gate(product_release_id, actor_user_id=current_user.id)
        )
    except (NotFoundException, ConflictException) as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.post("/product-releases/{product_release_id}/gate/approve", response_model=ReleaseGateDetailRead)
def approve_release_gate(
    product_release_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReleaseGateDetailRead:
    require_permissions(current_user, {Permission.release_lifecycle_write})
    service = ReleaseGateService(db)
    try:
        return ReleaseGateDetailRead.model_validate(
            service.approve_gate(product_release_id, actor_user_id=current_user.id)
        )
    except (NotFoundException, ConflictException) as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.post("/product-releases/{product_release_id}/gate/items/{gate_item_id}/evidence", response_model=ReleaseGateDetailRead)
def attach_artifact_to_gate_item(
    product_release_id: UUID,
    gate_item_id: UUID,
    payload: ArtifactCreateLinkRevisionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReleaseGateDetailRead:
    require_permissions(current_user, {Permission.release_write, Permission.evidence_item_write})
    service = ReleaseGateService(db)
    try:
        return ReleaseGateDetailRead.model_validate(
            service.attach_revision(
                product_release_id,
                gate_item_id,
                payload.artifact_revision_id,
                actor_user_id=current_user.id,
            )
        )
    except (NotFoundException, ConflictException) as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.post("/product-releases/{product_release_id}/gate/items/{gate_item_id}/upload", response_model=ReleaseGateDetailRead)
async def upload_evidence_for_gate_item(
    product_release_id: UUID,
    gate_item_id: UUID,
    title: str = Form(...),
    artifact_type: EvidenceType = Form(...),
    description: str | None = Form(default=None),
    change_summary: str | None = Form(default=None),
    upload: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReleaseGateDetailRead:
    require_permissions(current_user, {Permission.release_write, Permission.evidence_item_write})
    service = ReleaseGateService(db)
    try:
        return ReleaseGateDetailRead.model_validate(
            await service.upload_and_attach_evidence(
                product_release_id,
                gate_item_id,
                actor_user_id=current_user.id,
                title=title,
                artifact_type=artifact_type,
                upload=upload,
                description=description,
                change_summary=change_summary,
            )
        )
    except (NotFoundException, ConflictException) as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.post("/product-releases/{product_release_id}/gate/items/{gate_item_id}/link", response_model=ReleaseGateDetailRead)
def add_external_evidence_for_gate_item(
    product_release_id: UUID,
    gate_item_id: UUID,
    title: str = Form(...),
    artifact_type: EvidenceType = Form(...),
    external_url: str = Form(...),
    description: str | None = Form(default=None),
    change_summary: str | None = Form(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReleaseGateDetailRead:
    require_permissions(current_user, {Permission.release_write, Permission.evidence_item_write})
    service = ReleaseGateService(db)
    try:
        return ReleaseGateDetailRead.model_validate(
            service.create_and_attach_external_evidence(
                product_release_id,
                gate_item_id,
                actor_user_id=current_user.id,
                title=title,
                artifact_type=artifact_type,
                external_url=external_url,
                description=description,
                change_summary=change_summary,
            )
        )
    except (NotFoundException, ConflictException) as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.delete("/release-gate-evidence/{link_id}", response_model=ReleaseGateDetailRead)
def detach_evidence_from_gate_item(
    link_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReleaseGateDetailRead:
    require_permissions(current_user, {Permission.release_write, Permission.evidence_item_write})
    service = ReleaseGateService(db)
    try:
        return ReleaseGateDetailRead.model_validate(
            service.detach_revision(link_id, actor_user_id=current_user.id)
        )
    except (NotFoundException, ConflictException) as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.post("/release-gate-evidence/{link_id}/review", response_model=ReleaseGateDetailRead)
def review_gate_evidence(
    link_id: UUID,
    payload: ReleaseGateReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReleaseGateDetailRead:
    require_permissions(current_user, {Permission.release_lifecycle_write})
    service = ReleaseGateService(db)
    try:
        return ReleaseGateDetailRead.model_validate(
            service.review_link(
                link_id,
                decision=payload.decision,
                rationale=payload.rationale,
                actor_user_id=current_user.id,
            )
        )
    except (NotFoundException, ConflictException) as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.post("/product-releases/{product_release_id}/gate/items", response_model=ReleaseGateDetailRead)
def add_gate_checklist_item(
    product_release_id: UUID,
    payload: GateItemCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReleaseGateDetailRead:
    require_permissions(current_user, {Permission.release_write})
    service = ReleaseGateService(db)
    try:
        return ReleaseGateDetailRead.model_validate(
            service.add_custom_gate_item(
                product_release_id,
                title=payload.title,
                description=payload.description,
                actor_user_id=current_user.id,
            )
        )
    except (NotFoundException, ConflictException) as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.delete("/product-releases/{product_release_id}/gate/items/{gate_item_id}", response_model=ReleaseGateDetailRead)
def remove_gate_checklist_item(
    product_release_id: UUID,
    gate_item_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReleaseGateDetailRead:
    require_permissions(current_user, {Permission.release_write})
    service = ReleaseGateService(db)
    try:
        return ReleaseGateDetailRead.model_validate(
            service.remove_gate_item(
                product_release_id,
                gate_item_id,
                actor_user_id=current_user.id,
            )
        )
    except (NotFoundException, ConflictException) as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.get("/product-releases/{product_release_id}/gate/bundle")
def download_gate_bundle(
    product_release_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    require_permissions(current_user, {Permission.release_lifecycle_write})
    service = ReleaseGateService(db)
    try:
        zip_bytes, _, filename = service.get_bundle(product_release_id)
    except (NotFoundException, ConflictException) as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/product-releases/{product_release_id}/gate/prerequisites", response_model=ReleaseGateDetailRead)
def add_gate_item_prerequisite(
    product_release_id: UUID,
    dependent_item_id: UUID,
    prerequisite_item_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReleaseGateDetailRead:
    require_permissions(current_user, {Permission.release_write})
    service = ReleaseGateService(db)
    try:
        return ReleaseGateDetailRead.model_validate(
            service.add_prerequisite(
                product_release_id,
                dependent_item_id,
                prerequisite_item_id,
                actor_user_id=current_user.id,
            )
        )
    except (NotFoundException, ConflictException) as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.delete("/product-releases/{product_release_id}/gate/prerequisites", response_model=ReleaseGateDetailRead)
def remove_gate_item_prerequisite(
    product_release_id: UUID,
    dependent_item_id: UUID,
    prerequisite_item_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReleaseGateDetailRead:
    require_permissions(current_user, {Permission.release_write})
    service = ReleaseGateService(db)
    try:
        return ReleaseGateDetailRead.model_validate(
            service.remove_prerequisite(
                product_release_id,
                dependent_item_id,
                prerequisite_item_id,
                actor_user_id=current_user.id,
            )
        )
    except (NotFoundException, ConflictException) as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@router.get("/product-releases/{product_release_id}/gate/snapshot")
def get_gate_snapshot(
    product_release_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    require_permissions(current_user, {Permission.release_read})
    service = ReleaseGateService(db)
    try:
        gate = service.gate_repository.get_or_404_by_product_release_id(product_release_id)
        return {
            "snapshot": gate.snapshot_json,
            "bundle_sha256": gate.bundle_sha256,
            "approved_at": gate.approved_at,
            "approved_by_user_id": gate.approved_by_user_id,
        }
    except NotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
