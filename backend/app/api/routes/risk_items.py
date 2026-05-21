from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.exceptions import ConflictException, NotFoundException
from app.core.permissions import Permission, require_permissions
from app.models.user import User
from app.schemas.risk_item import RiskItemCreate, RiskItemRead, RiskItemUpdate
from app.services.risk_item_service import RiskItemService

router = APIRouter()


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("", response_model=list[RiskItemRead])
def list_risk_items(
    risk_assessment_id: UUID = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[RiskItemRead]:
    require_permissions(current_user, {Permission.risk_item_read})

    service = RiskItemService(db)
    return service.list_by_assessment(risk_assessment_id)


@router.get("/{risk_item_id}", response_model=RiskItemRead)
def get_risk_item(
    risk_item_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RiskItemRead:
    require_permissions(current_user, {Permission.risk_item_read})

    service = RiskItemService(db)
    return service.get(risk_item_id)


@router.post("", response_model=RiskItemRead, status_code=status.HTTP_201_CREATED)
def create_risk_item(
    payload: RiskItemCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RiskItemRead:
    require_permissions(current_user, {Permission.risk_item_write})

    service = RiskItemService(db)
    return service.create(
        payload,
        actor_user_id=current_user.id,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )


@router.patch("/{risk_item_id}", response_model=RiskItemRead)
def update_risk_item(
    risk_item_id: UUID,
    payload: RiskItemUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RiskItemRead:
    require_permissions(current_user, {Permission.risk_item_write})

    service = RiskItemService(db)
    return service.update(
        risk_item_id,
        payload,
        actor_user_id=current_user.id,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )


@router.delete(
    "/{risk_item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_risk_item(
    risk_item_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    require_permissions(current_user, {Permission.risk_item_write})

    service = RiskItemService(db)
    service.delete(
        risk_item_id,
        actor_user_id=current_user.id,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)