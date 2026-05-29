from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.core.permissions import Permission
from app.models.user import User
from app.schemas.remote_processing_element import (
    RemoteProcessingAssessRequest,
    RemoteProcessingElementCreate,
    RemoteProcessingElementRead,
    RemoteProcessingElementUpdate,
)
from app.services.remote_processing_element_service import RemoteProcessingElementService

router = APIRouter()


@router.get("/", response_model=list[RemoteProcessingElementRead])
def list_remote_processing_elements(
    product_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.remote_processing_element_read)),
) -> list[RemoteProcessingElementRead]:
    return RemoteProcessingElementService(db).list_elements(product_id=product_id)


@router.post("/", response_model=RemoteProcessingElementRead, status_code=status.HTTP_201_CREATED)
def create_remote_processing_element(
    payload: RemoteProcessingElementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.remote_processing_element_write)),
) -> RemoteProcessingElementRead:
    return RemoteProcessingElementService(db).create_element(payload, actor=current_user)


@router.get("/{element_id}", response_model=RemoteProcessingElementRead)
def get_remote_processing_element(
    element_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.remote_processing_element_read)),
) -> RemoteProcessingElementRead:
    return RemoteProcessingElementService(db).get_element(element_id)


@router.put("/{element_id}", response_model=RemoteProcessingElementRead)
def update_remote_processing_element(
    element_id: UUID,
    payload: RemoteProcessingElementUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.remote_processing_element_write)),
) -> RemoteProcessingElementRead:
    return RemoteProcessingElementService(db).update_element(element_id, payload, actor=current_user)


@router.post("/{element_id}/assess", response_model=RemoteProcessingElementRead)
def assess_remote_processing_element(
    element_id: UUID,
    payload: RemoteProcessingAssessRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.remote_processing_element_write)),
) -> RemoteProcessingElementRead:
    """Run the CRA Art. 3(2) evaluation wizard and persist the classification."""
    return RemoteProcessingElementService(db).assess_element(element_id, payload, actor=current_user)


@router.delete("/{element_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_remote_processing_element(
    element_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.remote_processing_element_write)),
) -> Response:
    RemoteProcessingElementService(db).delete_element(element_id, actor=current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)