"""Add sbom-tools analysis fields to sbom_records.

Adds: sbom_content (raw file text), quality_score (0-100 int),
      analysis_findings (JSONB output from sbom-tools validate + quality).

Revision ID: 20260510_0028
Revises: 20260510_0027
Create Date: 2026-05-10
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "20260510_0028"
down_revision = "20260510_0027"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sbom_records", sa.Column("sbom_content", sa.Text(), nullable=True))
    op.add_column("sbom_records", sa.Column("quality_score", sa.Integer(), nullable=True))
    op.add_column("sbom_records", sa.Column("analysis_findings", JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("sbom_records", "analysis_findings")
    op.drop_column("sbom_records", "quality_score")
    op.drop_column("sbom_records", "sbom_content")
