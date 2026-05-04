from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import require_permissions_dependency
from app.core.database import get_db
from app.core.permissions import Permission
from app.models.user import User
from app.schemas.security_advisory import (
    SecurityAdvisoryCreate,
    SecurityAdvisoryRead,
    SecurityAdvisoryUpdate,
)
from app.services.security_advisory_service import SecurityAdvisoryService

router = APIRouter()


@router.get("/", response_model=list[SecurityAdvisoryRead])
def list_security_advisories(
    product_release_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.security_update_read)),
) -> list[SecurityAdvisoryRead]:
    return SecurityAdvisoryService(db).list_security_advisories(
        product_release_id=product_release_id
    )


@router.post("/", response_model=SecurityAdvisoryRead, status_code=status.HTTP_201_CREATED)
def create_security_advisory(
    payload: SecurityAdvisoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.security_update_write)),
) -> SecurityAdvisoryRead:
    return SecurityAdvisoryService(db).create_security_advisory(payload, actor=current_user)


@router.get("/{advisory_id}", response_model=SecurityAdvisoryRead)
def get_security_advisory(
    advisory_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.security_update_read)),
) -> SecurityAdvisoryRead:
    return SecurityAdvisoryService(db).get_security_advisory(advisory_id)


@router.put("/{advisory_id}", response_model=SecurityAdvisoryRead)
def update_security_advisory(
    advisory_id: UUID,
    payload: SecurityAdvisoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.security_update_write)),
) -> SecurityAdvisoryRead:
    return SecurityAdvisoryService(db).update_security_advisory(
        advisory_id, payload, actor=current_user
    )


@router.delete(
    "/{advisory_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
def delete_security_advisory(
    advisory_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.security_update_write)),
) -> Response:
    SecurityAdvisoryService(db).delete_security_advisory(advisory_id, actor=current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
