"""Add product lifecycle obligation tier (legacy | active).

Distinguishes CRA obligation level per product: "legacy" products (on the market
before full CRA applicability, not substantially modified) carry reporting-only
obligations; "active" products carry the full set. Backfills existing pre-CRA
products to "legacy".

Revision ID: 20260628_0059
Revises: 20260628_0058
Create Date: 2026-06-28
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260628_0059"
down_revision = "20260628_0058"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    product_lifecycle_status = postgresql.ENUM(
        "legacy",
        "active",
        name="productlifecyclestatus",
        create_type=False,
    )
    product_lifecycle_status.create(bind, checkfirst=True)

    op.add_column(
        "products",
        sa.Column(
            "lifecycle_status",
            product_lifecycle_status,
            nullable=False,
            server_default="active",
        ),
    )
    op.create_index("ix_products_lifecycle_status", "products", ["lifecycle_status"])

    # Backfill: products already flagged pre-CRA start as "legacy".
    op.execute("UPDATE products SET lifecycle_status = 'legacy' WHERE is_pre_cra = true")


def downgrade() -> None:
    op.drop_index("ix_products_lifecycle_status", table_name="products")
    op.drop_column("products", "lifecycle_status")
    postgresql.ENUM(name="productlifecyclestatus").drop(op.get_bind(), checkfirst=True)
