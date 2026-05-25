from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response, status
from fastapi.exceptions import HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.exceptions import ConflictException, NotFoundException
from app.core.permissions import Permission, require_permissions
from app.models.user import User
from app.schemas.requirement_mapping import (
    RequirementMappingArtifactLinkRequest,
    RequirementMappingCreate,
    RequirementMappingRead,
    RequirementMappingMatrixRead,
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
    release_id: UUID | None = Query(default=None),
    matrix: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[RequirementMappingRead]:
    require_permissions(current_user, {Permission.requirement_mapping_read})

    service = RequirementMappingService(db)
    return service.list(
        risk_item_id=risk_item_id,
        annex_requirement_id=annex_requirement_id,
        release_id=release_id,
        matrix=matrix,
    )



@router.get("/{mapping_id}", response_model=RequirementMappingRead)
def get_requirement_mapping(
    mapping_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RequirementMappingRead:
    require_permissions(current_user, {Permission.requirement_mapping_read})

    service = RequirementMappingService(db)
    return service.get(mapping_id)


@router.post("/{mapping_id}/artifacts", response_model=RequirementMappingMatrixRead)
def attach_artifact_to_requirement_mapping(
    mapping_id: UUID,
    payload: RequirementMappingArtifactLinkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RequirementMappingMatrixRead:
    require_permissions(current_user, {Permission.requirement_mapping_write})
    service = RequirementMappingService(db)
    return RequirementMappingMatrixRead.model_validate(
        service.attach_artifact(mapping_id, payload.artifact_id, actor_user_id=current_user.id)
    )


@router.delete("/{mapping_id}/artifacts/{artifact_id}", response_model=RequirementMappingMatrixRead)
def detach_artifact_from_requirement_mapping(
    mapping_id: UUID,
    artifact_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RequirementMappingMatrixRead:
    require_permissions(current_user, {Permission.requirement_mapping_write})
    service = RequirementMappingService(db)
    return RequirementMappingMatrixRead.model_validate(
        service.detach_artifact(mapping_id, artifact_id, actor_user_id=current_user.id)
    )


@router.post("", response_model=RequirementMappingRead, status_code=status.HTTP_201_CREATED)
def create_requirement_mapping(
    payload: RequirementMappingCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RequirementMappingRead:
    require_permissions(current_user, {Permission.requirement_mapping_write})

    service = RequirementMappingService(db)
    return service.create(
        payload,
        actor_user_id=current_user.id,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )


@router.patch("/{mapping_id}", response_model=RequirementMappingRead)
def update_requirement_mapping(
    mapping_id: UUID,
    payload: RequirementMappingUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RequirementMappingRead:
    user_roles = set(current_user.role_names)

    if "admin" in user_roles or "cybersecurity_engineer" in user_roles:
        pass
    elif "product_owner" in user_roles:
        update_data = payload.model_dump(exclude_unset=True)
        allowed_fields = {"engineering_requirement_ref"}
        disallowed_fields = set(update_data.keys()) - allowed_fields
        if disallowed_fields:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Product owners may only update engineering_requirement_ref.",
            )
    else:
        require_permissions(current_user, {Permission.requirement_mapping_write})

    service = RequirementMappingService(db)
    return service.update(
        mapping_id,
        payload,
        actor_user_id=current_user.id,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )


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
    require_permissions(current_user, {Permission.requirement_mapping_write})

    service = RequirementMappingService(db)
    service.delete(
        mapping_id,
        actor_user_id=current_user.id,
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
