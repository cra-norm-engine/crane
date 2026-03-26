from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import require_permissions_dependency
from app.core.database import get_db
from app.core.permissions import Permission
from app.models.user import User
from app.schemas.product_release import ProductReleaseCreate, ProductReleaseRead, ProductReleaseUpdate
from app.services.product_release_service import ProductReleaseService

router = APIRouter()


@router.get("/", response_model=list[ProductReleaseRead])
def list_product_releases(
    product_id: UUID | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.release_read)),
) -> list[ProductReleaseRead]:
    return ProductReleaseService(db).list_releases(product_id=product_id)


@router.post("/", response_model=ProductReleaseRead, status_code=status.HTTP_201_CREATED)
def create_product_release(
    payload: ProductReleaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.release_write)),
) -> ProductReleaseRead:
    return ProductReleaseService(db).create_release(payload, actor=current_user)


@router.get("/{release_id}", response_model=ProductReleaseRead)
def get_product_release(
    release_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.release_read)),
) -> ProductReleaseRead:
    return ProductReleaseService(db).get_release(release_id)


@router.put("/{release_id}", response_model=ProductReleaseRead)
def update_product_release(
    release_id: UUID,
    payload: ProductReleaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.release_write)),
) -> ProductReleaseRead:
    return ProductReleaseService(db).update_release(release_id, payload, actor=current_user)


@router.delete("/{release_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_product_release(
    release_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permissions_dependency(Permission.release_write)),
) -> Response:
    ProductReleaseService(db).delete_release(release_id, actor=current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)