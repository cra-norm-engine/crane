from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.exceptions import ConflictException, NotFoundException
from app.core.permissions import Permission, require_permissions
from app.models.user import User
from app.schemas.risk_assessment import (
    RiskAssessmentApproveRequest,
    RiskAssessmentCreate,
    RiskAssessmentDetailRead,
    RiskAssessmentDuplicateVersionRequest,
    RiskAssessmentRead,
    RiskAssessmentRejectRequest,
    RiskAssessmentUpdate,
)
from app.services.risk_assessment_service import RiskAssessmentService

router = APIRouter()


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("", response_model=list[RiskAssessmentRead])
def list_risk_assessments(
    product_id: UUID | None = Query(default=None),
    product_release_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[RiskAssessmentRead]:
    require_permissions(current_user, {Permission.risk_assessment_read})

    service = RiskAssessmentService(db)
    try:
        return service.list(product_id=product_id, product_release_id=product_release_id)
    except ConflictException as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{assessment_id}", response_model=RiskAssessmentDetailRead)
def get_risk_assessment(
    assessment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RiskAssessmentDetailRead:
    require_permissions(current_user, {Permission.risk_assessment_read})

    service = RiskAssessmentService(db)
    try:
        return service.get(assessment_id)
    except NotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("", response_model=RiskAssessmentRead, status_code=status.HTTP_201_CREATED)
def create_risk_assessment(
    payload: RiskAssessmentCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RiskAssessmentRead:
    require_permissions(current_user, {Permission.risk_assessment_write})

    service = RiskAssessmentService(db)
    try:
        return service.create(
            payload,
            actor_user_id=current_user.id,
            ip_address=_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
    except NotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConflictException as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.patch("/{assessment_id}", response_model=RiskAssessmentRead)
def update_risk_assessment(
    assessment_id: UUID,
    payload: RiskAssessmentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RiskAssessmentRead:
    require_permissions(current_user, {Permission.risk_assessment_write})

    service = RiskAssessmentService(db)
    try:
        return service.update(
            assessment_id,
            payload,
            actor_user_id=current_user.id,
            ip_address=_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
    except NotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConflictException as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{assessment_id}/approve", response_model=RiskAssessmentRead)
def approve_risk_assessment(
    assessment_id: UUID,
    payload: RiskAssessmentApproveRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RiskAssessmentRead:
    require_permissions(current_user, {Permission.risk_assessment_write})

    service = RiskAssessmentService(db)
    try:
        return service.approve(
            assessment_id,
            payload,
            actor_user_id=current_user.id,
            ip_address=_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
    except NotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{assessment_id}/submit", response_model=RiskAssessmentRead)
def submit_risk_assessment_for_review(
    assessment_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RiskAssessmentRead:
    """
    Transition a risk assessment from draft → in_review.

    The calling user must have risk_assessment_write permission.
    Returns 409 if the assessment is not currently in draft status.
    """
    require_permissions(current_user, {Permission.risk_assessment_write})

    service = RiskAssessmentService(db)
    try:
        return service.submit_for_review(
            assessment_id,
            actor_user_id=current_user.id,
            ip_address=_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
    except NotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConflictException as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/{assessment_id}/reject", response_model=RiskAssessmentRead)
def reject_risk_assessment(
    assessment_id: UUID,
    payload: RiskAssessmentRejectRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RiskAssessmentRead:
    """
    Transition a risk assessment from in_review → draft with a rejection reason.

    The calling user must have risk_assessment_write permission.
    Returns 409 if the assessment is not currently in in_review status.
    """
    require_permissions(current_user, {Permission.risk_assessment_write})

    service = RiskAssessmentService(db)
    try:
        return service.reject_assessment(
            assessment_id,
            payload.rejection_reason,
            actor_user_id=current_user.id,
            ip_address=_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
    except NotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConflictException as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post(
    "/{assessment_id}/duplicate-version",
    response_model=RiskAssessmentRead,
    status_code=status.HTTP_201_CREATED,
)
def duplicate_risk_assessment_version(
    assessment_id: UUID,
    payload: RiskAssessmentDuplicateVersionRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RiskAssessmentRead:
    require_permissions(current_user, {Permission.risk_assessment_write})

    service = RiskAssessmentService(db)
    try:
        return service.duplicate_version(
            assessment_id,
            payload,
            actor_user_id=current_user.id,
            ip_address=_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
    except NotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConflictException as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.delete("/{assessment_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_risk_assessment(
    assessment_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    require_permissions(current_user, {Permission.risk_assessment_write})

    service = RiskAssessmentService(db)
    try:
        service.delete(
            assessment_id,
            actor_user_id=current_user.id,
            ip_address=_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
    except NotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)
