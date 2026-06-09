"""support period: unique active record per release instead of per product

Revision ID: 20260609_0049
Revises: 20260606_0048
Create Date: 2026-06-09 00:00:00

Support periods are now assigned per release. The old partial unique index
only allowed one active record per product (regardless of release). The new
index allows one active record per (product, release) pair, enabling each
release to have its own independent support window.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260609_0049"
down_revision = "20260606_0048"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the old product-level uniqueness constraint.
    op.drop_index(
        "ix_support_period_records_one_active_per_product",
        table_name="support_period_records",
    )
    # Create a per-release uniqueness constraint: at most one active support
    # period record per (product_id, product_release_id) combination.
    op.create_index(
        "ix_support_period_records_one_active_per_release",
        "support_period_records",
        ["product_id", "product_release_id"],
        unique=True,
        postgresql_where=sa.text("is_active = true"),
    )


def downgrade() -> None:
    op.drop_index(
        "ix_support_period_records_one_active_per_release",
        table_name="support_period_records",
    )
    op.create_index(
        "ix_support_period_records_one_active_per_product",
        "support_period_records",
        ["product_id"],
        unique=True,
        postgresql_where=sa.text("is_active = true"),
    )
