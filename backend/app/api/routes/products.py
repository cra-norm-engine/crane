from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, require_permission
from app.core.database import get_db
from app.core.permissions import Permission
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate
from app.services.product_service import ProductService

router = APIRouter()


@router.get("/", response_model=list[ProductRead])
def list_products(
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permission(Permission.product_read)),
) -> list[ProductRead]:
    return ProductService(db).list_products()


@router.post("/", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_permission(Permission.product_write)),
) -> ProductRead:
    return ProductService(db).create_product(payload, actor=user)


@router.get("/{product_id}", response_model=ProductRead)
def get_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    _: CurrentUser = Depends(require_permission(Permission.product_read)),
) -> ProductRead:
    return ProductService(db).get_product(product_id)


@router.put("/{product_id}", response_model=ProductRead)
def update_product(
    product_id: UUID,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_permission(Permission.product_write)),
) -> ProductRead:
    return ProductService(db).update_product(product_id, payload, actor=user)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(require_permission(Permission.product_write)),
) -> Response:
    ProductService(db).delete_product(product_id, actor=user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
