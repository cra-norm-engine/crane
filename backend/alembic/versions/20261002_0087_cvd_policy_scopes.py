"""allow organization-wide and multi-product CVD policies

Revision ID: 20261002_0087
Revises: 20260925_0086
"""

from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20261002_0087"
down_revision = "20260925_0086"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "cvd_policies",
        sa.Column(
            "organization_wide", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
    )
    op.create_table(
        "cvd_policy_products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cvd_policy_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["cvd_policy_id"], ["cvd_policies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.UniqueConstraint(
            "cvd_policy_id", "product_id", name="uq_cvd_policy_products_policy_product"
        ),
    )
    op.create_index(
        "ix_cvd_policy_products_cvd_policy_id", "cvd_policy_products", ["cvd_policy_id"]
    )
    op.create_index("ix_cvd_policy_products_product_id", "cvd_policy_products", ["product_id"])
    op.execute(
        """
        INSERT INTO cvd_policy_products (id, created_at, updated_at, cvd_policy_id, product_id)
        SELECT gen_random_uuid(), now(), now(), id, product_id FROM cvd_policies
        """
    )
    op.drop_index("ix_cvd_policies_product_id", table_name="cvd_policies")
    op.drop_constraint("cvd_policies_product_id_fkey", "cvd_policies", type_="foreignkey")
    op.drop_column("cvd_policies", "product_id")


def downgrade() -> None:
    op.add_column(
        "cvd_policies", sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.execute(
        """
        UPDATE cvd_policies AS policy
        SET product_id = links.product_id
        FROM (
            SELECT DISTINCT ON (cvd_policy_id) cvd_policy_id, product_id
            FROM cvd_policy_products
            ORDER BY cvd_policy_id, created_at
        ) AS links
        WHERE policy.id = links.cvd_policy_id
        """
    )
    op.execute("DELETE FROM cvd_policies WHERE product_id IS NULL")
    op.alter_column("cvd_policies", "product_id", nullable=False)
    op.create_foreign_key(
        "cvd_policies_product_id_fkey",
        "cvd_policies",
        "products",
        ["product_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_cvd_policies_product_id", "cvd_policies", ["product_id"])
    op.drop_table("cvd_policy_products")
    op.drop_column("cvd_policies", "organization_wide")
