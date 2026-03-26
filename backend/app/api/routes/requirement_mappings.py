from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.exceptions import ConflictException, NotFoundException
from app.core.permissions import (
    Permission,
    ROLE_ADMIN,
    ROLE_CYBERSECURITY_ENGINEER,
    ROLE_PRODUCT_OWNER,
    require_permissions,
)
from app.models.user import User
from app.schemas.requirement_mapping import (
    RequirementMappingCreate,
    RequirementMappingRead,
    RequirementMappingUpdate,
)
from app.services.requirement_mapping_service import RequirementMappingService

router = APIRouter()


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("", response_model=list[RequirementMappingRead])
def list_requirement_mappings(
    risk_item_id: UUID | None = Query(default=None),
    annex_requirement_id: UUID | None = Query(default=None),
    matrix: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[RequirementMappingRead]:
    require_permissions(current_user.role_names, {Permission.requirement_mapping_read})

    service = RequirementMappingService(db)
    try:
        return service.list(
            risk_item_id=risk_item_id,
            annex_requirement_id=annex_requirement_id,
            matrix=matrix,
        )
    except ConflictException as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{mapping_id}", response_model=RequirementMappingRead)
def get_requirement_mapping(
    mapping_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RequirementMappingRead:
    require_permissions(current_user.role_names, {Permission.requirement_mapping_read})

    service = RequirementMappingService(db)
    try:
        return service.get(mapping_id)
    except NotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("", response_model=RequirementMappingRead, status_code=status.HTTP_201_CREATED)
def create_requirement_mapping(
    payload: RequirementMappingCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RequirementMappingRead:
    require_permissions(current_user.role_names, {Permission.requirement_mapping_write})

    service = RequirementMappingService(db)
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


@router.patch("/{mapping_id}", response_model=RequirementMappingRead)
def update_requirement_mapping(
    mapping_id: UUID,
    payload: RequirementMappingUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RequirementMappingRead:
    user_roles = set(current_user.role_names)

    if ROLE_ADMIN in user_roles or ROLE_CYBERSECURITY_ENGINEER in user_roles:
        pass
    elif ROLE_PRODUCT_OWNER in user_roles:
        update_data = payload.model_dump(exclude_unset=True)
        allowed_fields = {"engineering_requirement_ref"}
        disallowed_fields = set(update_data.keys()) - allowed_fields
        if disallowed_fields:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Product owners may only update engineering_requirement_ref.",
            )
    else:
        require_permissions(current_user.role_names, {Permission.requirement_mapping_write})

    service = RequirementMappingService(db)
    try:
        return service.update(
            mapping_id,
            payload,
            actor_user_id=current_user.id,
            ip_address=_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
    except NotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConflictException as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.delete(
    "/{mapping_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_requirement_mapping(
    mapping_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    require_permissions(current_user.role_names, {Permission.requirement_mapping_write})

    service = RequirementMappingService(db)
    try:
        service.delete(
            mapping_id,
            actor_user_id=current_user.id,
            ip_address=_client_ip(request),
            user_agent=request.headers.get("user-agent"),
        )
    except NotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)