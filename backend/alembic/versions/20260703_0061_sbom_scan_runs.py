"""sbom scan runs — record of each automated/manual vulnerability scan execution

Revision ID: 20260703_0061
Revises: 20260628_0060
Create Date: 2026-07-03 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260703_0061"
down_revision = "20260628_0060"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sbom_scan_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "sbom_record_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sbom_records.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("trigger", sa.String(20), nullable=False, index=True),
        sa.Column("status", sa.String(20), nullable=False, index=True),
        sa.Column("findings_created", sa.Integer, nullable=False, server_default="0"),
        sa.Column("reports_created", sa.Integer, nullable=False, server_default="0"),
        sa.Column("components_scanned", sa.Integer, nullable=False, server_default="0"),
        sa.Column("nvd_enrichments", sa.Integer, nullable=False, server_default="0"),
        sa.Column("epss_enrichments", sa.Integer, nullable=False, server_default="0"),
        sa.Column("osv_reachable", sa.Boolean, nullable=False, server_default=sa.true()),
        sa.Column("trivy_available", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("error", sa.Text, nullable=True),
        sa.Column("duration_ms", sa.Integer, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("sbom_scan_runs")
