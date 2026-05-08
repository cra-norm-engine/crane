"""API routes for market actions (CRA Art. 35 recalls and withdrawals)."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import require_permissions_dependency
from app.core.database import get_db
from app.core.permissions import Permission
from app.models.enums import MarketActionStatus, MarketActionType
from app.models.user import User
from app.schemas.market_action import MarketActionCreate, MarketActionRead, MarketActionUpdate
from app.services.market_action_service import MarketActionService

router = APIRouter()


@router.get("/", response_model=list[MarketActionRead])
def list_market_actions(
    product_release_id: UUID | None = Query(default=None),
    action_type: MarketActionType | None = Query(default=None),
    status: MarketActionStatus | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.market_action_read)),
) -> list[MarketActionRead]:
    return MarketActionService(db).list_actions(
        product_release_id=product_release_id,
        action_type=action_type,
        status=status,
    )


@router.post("/", response_model=MarketActionRead, status_code=status.HTTP_201_CREATED)
def create_market_action(
    payload: MarketActionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.market_action_write)),
) -> MarketActionRead:
    return MarketActionService(db).create_action(payload, actor=current_user)


@router.get("/{action_id}", response_model=MarketActionRead)
def get_market_action(
    action_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.market_action_read)),
) -> MarketActionRead:
    return MarketActionService(db).get_action(action_id)


@router.put("/{action_id}", response_model=MarketActionRead)
def update_market_action(
    action_id: UUID,
    payload: MarketActionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.market_action_write)),
) -> MarketActionRead:
    return MarketActionService(db).update_action(action_id, payload, actor=current_user)


class AuthorityNotifiedRequest(BaseModel):
    notified_at: datetime | None = None


@router.post("/{action_id}/mark-authority-notified", response_model=MarketActionRead)
def mark_authority_notified(
    action_id: UUID,
    payload: AuthorityNotifiedRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.market_action_write)),
) -> MarketActionRead:
    return MarketActionService(db).mark_authority_notified(
        action_id, actor=current_user, notified_at=payload.notified_at
    )


@router.post("/{action_id}/close", response_model=MarketActionRead)
def close_market_action(
    action_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.market_action_write)),
) -> MarketActionRead:
    return MarketActionService(db).close_action(action_id, actor=current_user)


@router.delete("/{action_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_market_action(
    action_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.market_action_write)),
) -> Response:
    MarketActionService(db).delete_action(action_id, actor=current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
