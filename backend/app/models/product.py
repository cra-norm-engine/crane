from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDTimestampMixin
from app.models.enums import ConformityRoute, GateStatus, ProductClassification, ReleaseStatus
from app.models.user import User


class Product(UUIDTimestampMixin, Base):
    __tablename__ = "products"

    name: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    product_code: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    classification: Mapped[ProductClassification] = mapped_column(nullable=False, default=ProductClassification.normal)
    conformity_route: Mapped[ConformityRoute] = mapped_column(nullable=False, default=ConformityRoute.undecided)
    market_placement_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    support_period_months: Mapped[int | None] = mapped_column(Integer, nullable=True)

    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    owner: Mapped[User | None] = relationship(lazy="joined")

    releases: Mapped[list["ProductRelease"]] = relationship(
        back_populates="product",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class ProductRelease(UUIDTimestampMixin, Base):
    __tablename__ = "product_releases"
    __table_args__ = (UniqueConstraint("product_id", "version", name="uq_product_releases_product_version"),)

    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[str] = mapped_column(String(100), nullable=False)
    release_status: Mapped[ReleaseStatus] = mapped_column(nullable=False, default=ReleaseStatus.draft)
    release_gate_status: Mapped[GateStatus] = mapped_column(nullable=False, default=GateStatus.warning)
    known_exploitable_vulnerabilities_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    required_artifacts_complete: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    authority_package_generated_at: Mapped[datetime | None] = mapped_column(nullable=True)
    released_at: Mapped[datetime | None] = mapped_column(nullable=True)

    product: Mapped[Product] = relationship(back_populates="releases")