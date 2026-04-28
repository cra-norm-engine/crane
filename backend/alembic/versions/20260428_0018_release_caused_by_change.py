"""Add caused_by_change_id to product_releases.

Links a product release back to the substantial change (CRA Art. 13(8))
that required it to be re-released. NULL for all planned/routine releases.

Revision ID: 20260428_0018
Revises: 20260427_0017
Create Date: 2026-04-28
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# Alembic revision identifiers
revision = "20260428_0018"
down_revision = "20260427_0017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add the nullable FK column to product_releases
    op.add_column(
        "product_releases",
        sa.Column(
            "caused_by_change_id",
            sa.UUID(),
            nullable=True,
            comment="FK to changes.id — set when this release was triggered by a CRA substantial modification",
        ),
    )

    # Add the foreign key constraint with SET NULL so deleting a change
    # does not cascade-delete the release record
    op.create_foreign_key(
        "fk_product_releases_caused_by_change",
        "product_releases",
        "changes",
        ["caused_by_change_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Index for efficient lookups of "which releases were caused by change X"
    op.create_index(
        "ix_product_releases_caused_by_change_id",
        "product_releases",
        ["caused_by_change_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_product_releases_caused_by_change_id", table_name="product_releases")
    op.drop_constraint("fk_product_releases_caused_by_change", "product_releases", type_="foreignkey")
    op.drop_column("product_releases", "caused_by_change_id")
