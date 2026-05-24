"""add substantiality_analysis_id to product_releases

Art. 13(7) + Art. 3(30): v2+ releases must document whether the change
constitutes a substantial modification under CRA Art. 3(30). This FK links
a ProductRelease to the SubstantialModificationAssessment that recorded that
determination.

The release gate service auto-creates a 'substantial_modification_analysis'
gate item for any release where parent_release_id is set (v2+). The assessor
must link the completed assessment here before the gate can be approved.

Revision ID: 20260524_0038
Revises: 20260524_0037
Create Date: 2026-05-24
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260524_0038"
down_revision = "20260524_0037"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "product_releases",
        sa.Column(
            "substantiality_analysis_id",
            sa.UUID(),
            sa.ForeignKey("substantial_modification_assessments.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_product_releases_substantiality_analysis_id",
        "product_releases",
        ["substantiality_analysis_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_product_releases_substantiality_analysis_id", table_name="product_releases")
    op.drop_column("product_releases", "substantiality_analysis_id")
