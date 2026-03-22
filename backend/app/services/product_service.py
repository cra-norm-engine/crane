from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundException
from app.schemas.product import ProductCreate, ProductRead, ProductUpdate


class ProductService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_products(self) -> list[ProductRead]:
        return []

    def create_product(self, payload: ProductCreate, actor: dict[str, object]) -> ProductRead:
        raise NotImplementedError("Product creation scaffold not fully wired yet")

    def get_product(self, product_id: UUID) -> ProductRead:
        raise NotFoundException(f"Product {product_id} not found")

    def update_product(self, product_id: UUID, payload: ProductUpdate, actor: dict[str, object]) -> ProductRead:
        raise NotFoundException(f"Product {product_id} not found")

    def delete_product(self, product_id: UUID, actor: dict[str, object]) -> None:
        raise NotFoundException(f"Product {product_id} not found")
