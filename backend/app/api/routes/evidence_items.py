from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response, status
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.exceptions import ConflictException, NotFoundException
from app.core.permissions import Permission, require_permissions
from app.models.user import User
from app.schemas.evidence_item import EvidenceItemCreate, EvidenceItemRead, EvidenceItemUpdate
from app.services.evidence_item_service import EvidenceItemService

router = APIRouter()


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("", response_model=list[EvidenceItemRead])
def list_evidence_items(
    product_release_id: UUID | None = Query(default=None),
    risk_assessment_id: UUID | None = Query(default=None),
    requirement_mapping_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[EvidenceItemRead]:
    require_permissions(current_user, {Permission.evidence_item_read})

    if not any([product_release_id, risk_assessment_id, requirement_mapping_id]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="One of product_release_id, risk_assessment_id, or requirement_mapping_id must be provided.",
        )

    service = EvidenceItemService(db)
    return service.list(
        product_release_id=product_release_id,
        risk_assessment_id=risk_assessment_id,
        requirement_mapping_id=requirement_mapping_id,
    )


@router.get("/{evidence_item_id}", response_model=EvidenceItemRead)
def get_evidence_item(
    evidence_item_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EvidenceItemRead:
    require_permissions(current_user, {Permission.evidence_item_read})

    service = EvidenceItemService(db)
    return service.get(evidence_item_id)


@router.post("", response_model=EvidenceItemRead, status_code=status.HTTP_201_CREATED)
def create_evidence_item(
    payload: EvidenceItemCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EvidenceItemRead:
    require_permissions(current_user, {Permission.evidence_item_write})

    service = EvidenceItemService(db)
    return service.create(
        payload,
        actor_user_id=current_user.id,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )


@router.patch("/{evidence_item_id}", response_model=EvidenceItemRead)
def update_evidence_item(
    evidence_item_id: UUID,
    payload: EvidenceItemUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EvidenceItemRead:
    require_permissions(current_user, {Permission.evidence_item_write})

    service = EvidenceItemService(db)
    return service.update(
        evidence_item_id,
        payload,
        actor_user_id=current_user.id,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )


@router.delete(
    "/{evidence_item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_evidence_item(
    evidence_item_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    require_permissions(current_user, {Permission.evidence_item_write})

    service = EvidenceItemService(db)
    service.delete(
        evidence_item_id,
        actor_user_id=current_user.id,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)