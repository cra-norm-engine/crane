from __future__ import annotations

from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import NotFoundException
from app.models.product import Product
from app.repositories.base import BaseRepository


class ProductRepository(BaseRepository[Product]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Product)

    def list_all(self, *, search: str | None = None) -> list[Product]:
        statement = (
            select(Product)
            .options(
                selectinload(Product.child_products),
                selectinload(Product.releases),
                selectinload(Product.remote_processing_elements),
            )
            .order_by(Product.created_at.desc())
        )

        if search:
            like_term = f"%{search.strip()}%"
            statement = statement.where(
                or_(
                    Product.product_code.ilike(like_term),
                    Product.name.ilike(like_term),
                )
            )

        return list(self.db.scalars(statement).unique().all())

    def get_by_product_code(self, product_code: str) -> Product | None:
        statement = select(Product).where(Product.product_code == product_code)
        return self.db.scalar(statement)

    def get_detail_or_404(self, product_id: UUID) -> Product:
        statement = (
            select(Product)
            .options(
                selectinload(Product.child_products),
                selectinload(Product.releases),
                selectinload(Product.remote_processing_elements),
                selectinload(Product.scope_evaluations),
            )
            .where(Product.id == product_id)
        )
        product = self.db.scalar(statement)
        if product is None:
            raise NotFoundException("Product not found")
        return product

    def get_or_404(self, product_id: UUID) -> Product:
        product = self.get_by_id(product_id)
        if product is None:
            raise NotFoundException("Product not found")
        return product