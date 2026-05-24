"""add eu_doc fields to product_releases

CRA Art. 28 + Annex V: captures the EU Declaration of Conformity draw-up date,
reference number, and notified body for each product release.

eu_doc_date must be on or before placed_on_market_date (enforced at service layer).

Revision ID: 20260524_0036
Revises: 20260524_0035
Create Date: 2026-05-24
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260524_0036"
down_revision = "20260524_0035"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "product_releases",
        sa.Column("eu_doc_date", sa.Date(), nullable=True),
    )
    op.add_column(
        "product_releases",
        sa.Column("eu_doc_number", sa.String(100), nullable=True),
    )
    op.add_column(
        "product_releases",
        sa.Column("eu_doc_notified_body", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("product_releases", "eu_doc_notified_body")
    op.drop_column("product_releases", "eu_doc_number")
    op.drop_column("product_releases", "eu_doc_date")
