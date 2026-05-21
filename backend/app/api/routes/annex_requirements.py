from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.exceptions import ConflictException, NotFoundException
from app.core.permissions import Permission, require_permissions
from app.models.enums import AnnexPart
from app.models.user import User
from app.schemas.annex_requirement import (
    AnnexRequirementCreate,
    AnnexRequirementRead,
    AnnexRequirementUpdate,
)
from app.services.annex_requirement_service import AnnexRequirementService

router = APIRouter()


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("", response_model=list[AnnexRequirementRead])
def list_annex_requirements(
    annex_part: AnnexPart | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AnnexRequirementRead]:
    require_permissions(current_user, {Permission.annex_requirement_read})

    service = AnnexRequirementService(db)
    return service.list(
        annex_part=annex_part,
        is_active=is_active,
    )


@router.get("/{annex_requirement_id}", response_model=AnnexRequirementRead)
def get_annex_requirement(
    annex_requirement_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnnexRequirementRead:
    require_permissions(current_user, {Permission.annex_requirement_read})

    service = AnnexRequirementService(db)
    return service.get(annex_requirement_id)


@router.post("", response_model=AnnexRequirementRead, status_code=status.HTTP_201_CREATED)
def create_annex_requirement(
    payload: AnnexRequirementCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnnexRequirementRead:
    require_permissions(current_user, {Permission.annex_requirement_write})

    service = AnnexRequirementService(db)
    return service.create(
        payload,
        actor_user_id=current_user.id,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )


@router.patch("/{annex_requirement_id}", response_model=AnnexRequirementRead)
def update_annex_requirement(
    annex_requirement_id: UUID,
    payload: AnnexRequirementUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnnexRequirementRead:
    require_permissions(current_user, {Permission.annex_requirement_write})

    service = AnnexRequirementService(db)
    return service.update(
        annex_requirement_id,
        payload,
        actor_user_id=current_user.id,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )


@router.delete(
    "/{annex_requirement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_annex_requirement(
    annex_requirement_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    require_permissions(current_user, {Permission.annex_requirement_write})

    service = AnnexRequirementService(db)
    service.delete(
        annex_requirement_id,
        actor_user_id=current_user.id,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)