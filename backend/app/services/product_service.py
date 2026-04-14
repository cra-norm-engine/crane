from __future__ import annotations

from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.audit import create_audit_event
from app.core.exceptions import ConflictException
from app.models.enums import AuditStatus, EntityType
from app.models.product import Product
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCreate, ProductDetailRead, ProductRead, ProductSummaryRead, ProductUpdate


class ProductService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = ProductRepository(db)

    def list_products(self, *, search: str | None = None) -> list[ProductSummaryRead]:
        products = self.repository.list_all(search=search)
        return [ProductSummaryRead.model_validate(product) for product in products]

    def create_product(self, payload: ProductCreate, actor: object) -> ProductRead:
        if self.repository.get_by_product_code(payload.product_code):
            raise ConflictException("Product code already exists")

        if payload.parent_product_id:
            self.repository.get_or_404(payload.parent_product_id)

        product = Product(**payload.model_dump())

        try:
            self.repository.add(product)
            create_audit_event(
                self.db,
                actor_user_id=getattr(actor, "id", None),
                action_type="product.created",
                entity_type=EntityType.product,
                entity_id=product.id,
                status=AuditStatus.success,
                details_json={
                    "product_code": product.product_code,
                    "name": product.name,
                    "product_id": str(product.id),
                    "product_name": product.name,
                },
            )
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictException("Unable to create product due to uniqueness conflict") from exc

        return ProductRead.model_validate(product)

    def get_product(self, product_id: UUID) -> ProductDetailRead:
        product = self.repository.get_detail_or_404(product_id)
        return ProductDetailRead.model_validate(product)

    def update_product(self, product_id: UUID, payload: ProductUpdate, actor: object) -> ProductRead:
        product = self.repository.get_or_404(product_id)
        updates = payload.model_dump(exclude_unset=True)

        if "parent_product_id" in updates and updates["parent_product_id"]:
            self.repository.get_or_404(updates["parent_product_id"])
            if updates["parent_product_id"] == product.id:
                raise ConflictException("A product cannot be its own parent")

        for field_name, value in updates.items():
            setattr(product, field_name, value)

        try:
            self.db.flush()
            create_audit_event(
                self.db,
                actor_user_id=getattr(actor, "id", None),
                action_type="product.updated",
                entity_type=EntityType.product,
                entity_id=product.id,
                status=AuditStatus.success,
                details_json={
                    "product_id": str(product.id),
                    "product_code": product.product_code,
                    "product_name": product.name,
                    "updated_fields": sorted(updates.keys()),
                },
            )
            self.db.commit()
            self.db.refresh(product)
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictException("Unable to update product due to uniqueness conflict") from exc

        return ProductRead.model_validate(product)

    def delete_product(self, product_id: UUID, actor: object) -> None:
        product = self.repository.get_or_404(product_id)

        self.repository.delete(product)
        create_audit_event(
            self.db,
            actor_user_id=getattr(actor, "id", None),
            action_type="product.deleted",
            entity_type=EntityType.product,
            entity_id=product.id,
            status=AuditStatus.success,
            details_json={
                "product_id": str(product.id),
                "product_code": product.product_code,
                "name": product.name,
                "product_name": product.name,
            },
        )
        self.db.commit()
