"""DoC workflow fields + manufacturer address

CRA Art. 28 / Annex V: supports a signable EU Declaration of Conformity.

Adds:
  * products.manufacturer_address — Annex V(2) registered trade address (free text).
  * product_releases.eu_doc_approved_by / eu_doc_approved_at — internal approval record.
  * product_releases.eu_doc_signed_at — timestamp the DoC was formally drawn up.
  * a default of "draft" for the existing eu_doc_status column so the DoC lifecycle
    (draft -> approved -> signed) has a well-defined starting state.

Revision ID: 20260713_0063
Revises: 20260704_0062
Create Date: 2026-07-13
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260713_0063"
down_revision = "20260704_0062"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Annex V(2) manufacturer registered trade address.
    op.add_column(
        "products",
        sa.Column("manufacturer_address", sa.Text(), nullable=True),
    )
    # DoC approval / signature audit fields.
    op.add_column(
        "product_releases",
        sa.Column("eu_doc_approved_by", sa.String(255), nullable=True),
    )
    op.add_column(
        "product_releases",
        sa.Column("eu_doc_approved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "product_releases",
        sa.Column("eu_doc_signed_at", sa.DateTime(timezone=True), nullable=True),
    )
    # Give the existing free-text status column a defined default ("draft") going
    # forward. Existing NULL rows are treated as "draft" at the service layer.
    op.alter_column(
        "product_releases",
        "eu_doc_status",
        server_default="draft",
        existing_type=sa.String(50),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "product_releases",
        "eu_doc_status",
        server_default=None,
        existing_type=sa.String(50),
        existing_nullable=True,
    )
    op.drop_column("product_releases", "eu_doc_signed_at")
    op.drop_column("product_releases", "eu_doc_approved_at")
    op.drop_column("product_releases", "eu_doc_approved_by")
    op.drop_column("products", "manufacturer_address")
