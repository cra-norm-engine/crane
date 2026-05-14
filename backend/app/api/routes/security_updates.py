from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import require_permissions_dependency
from app.core.database import get_db
from app.core.permissions import Permission
from app.models.user import User
from app.schemas.security_update import SecurityUpdateCreate, SecurityUpdateRead, SecurityUpdateUpdate
from app.services.security_update_service import SecurityUpdateService

router = APIRouter()


@router.get("/", response_model=list[SecurityUpdateRead])
def list_security_updates(
    product_release_id: UUID | None = Query(default=None),
    product_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.security_update_read)),
) -> list[SecurityUpdateRead]:
    return SecurityUpdateService(db).list_security_updates(
        product_release_id=product_release_id,
        product_id=product_id,
    )


@router.post("/", response_model=SecurityUpdateRead, status_code=status.HTTP_201_CREATED)
def create_security_update(
    payload: SecurityUpdateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.security_update_write)),
) -> SecurityUpdateRead:
    return SecurityUpdateService(db).create_security_update(payload, actor=current_user)


@router.get("/{security_update_id}", response_model=SecurityUpdateRead)
def get_security_update(
    security_update_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.security_update_read)),
) -> SecurityUpdateRead:
    return SecurityUpdateService(db).get_security_update(security_update_id)


@router.put("/{security_update_id}", response_model=SecurityUpdateRead)
def update_security_update(
    security_update_id: UUID,
    payload: SecurityUpdateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.security_update_write)),
) -> SecurityUpdateRead:
    return SecurityUpdateService(db).update_security_update(
        security_update_id,
        payload,
        actor=current_user,
    )


@router.delete("/{security_update_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_security_update(
    security_update_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.security_update_write)),
) -> Response:
    SecurityUpdateService(db).delete_security_update(security_update_id, actor=current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)