from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.api.deps import require_permission
from app.core.database import get_db
from app.core.permissions import Permission
from app.models.user import User
from app.schemas.product import ProductCreate, ProductDetailRead, ProductRead, ProductSummaryRead, ProductUpdate
from app.schemas.scope_evaluation import ProductScopeEvaluationRead, ProductScopeEvaluationRequest
from app.services.product_service import ProductService
from app.services.scope_evaluation_service import ScopeEvaluationService

router = APIRouter()


@router.get("/", response_model=list[ProductSummaryRead])
def list_products(
    search: str | None = Query(default=None, max_length=255),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.product_read)),
) -> list[ProductSummaryRead]:
    return ProductService(db).list_products(search=search)


@router.post("/", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.product_write)),
) -> ProductRead:
    return ProductService(db).create_product(payload, actor=current_user)


@router.get("/{product_id}", response_model=ProductDetailRead)
def get_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.product_read)),
) -> ProductDetailRead:
    return ProductService(db).get_product(product_id)


@router.put("/{product_id}", response_model=ProductRead)
def update_product(
    product_id: UUID,
    payload: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.product_write)),
) -> ProductRead:
    return ProductService(db).update_product(product_id, payload, actor=current_user)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_product(
    product_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.product_write)),
) -> Response:
    ProductService(db).delete_product(product_id, actor=current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{product_id}/scope-evaluation",
    response_model=ProductScopeEvaluationRead,
    status_code=status.HTTP_201_CREATED,
)
def evaluate_scope(
    product_id: UUID,
    payload: ProductScopeEvaluationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.scope_evaluation_write)),
) -> ProductScopeEvaluationRead:
    return ScopeEvaluationService(db).evaluate_product_scope(
        product_id=product_id,
        payload=payload,
        actor=current_user,
    )