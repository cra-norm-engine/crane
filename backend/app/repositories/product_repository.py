from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.product import Product
from app.repositories.base import BaseRepository


class ProductRepository(BaseRepository[Product]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Product)

    def list_all(self) -> list[Product]:
        statement = select(Product).order_by(Product.created_at.desc())
        return list(self.db.scalars(statement).all())

    def get_by_product_code(self, product_code: str) -> Product | None:
        statement = select(Product).where(Product.product_code == product_code)
        return self.db.scalar(statement)

    def get_or_404(self, product_id: UUID) -> Product:
        product = self.get_by_id(product_id)
        if product is None:
            from app.core.exceptions import NotFoundException

            raise NotFoundException("Product not found")
        return product