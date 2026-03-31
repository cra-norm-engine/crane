"""fix support period versioning uniqueness

Revision ID: 20260405_0007
Revises: 20260404_0006
Create Date: 2026-04-05 00:00:00
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260405_0007"
down_revision = "20260404_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint(
        "uq_support_period_records_product_active",
        "support_period_records",
        type_="unique",
    )
    op.create_index(
        "ix_support_period_records_one_active_per_product",
        "support_period_records",
        ["product_id"],
        unique=True,
        postgresql_where=sa.text("is_active = true"),
    )


def downgrade() -> None:
    op.drop_index(
        "ix_support_period_records_one_active_per_product",
        table_name="support_period_records",
    )
    op.create_unique_constraint(
        "uq_support_period_records_product_active",
        "support_period_records",
        ["product_id", "is_active"],
    )
