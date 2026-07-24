"""add CISA KEV enrichment fields to SBOM vulnerability findings

Revision ID: 20260717_0065
Revises: 20260715_0064
Create Date: 2026-07-17

CISA's Known Exploited Vulnerabilities catalog identifies CVEs with public
evidence of exploitation in the wild. These columns retain the matching KEV
record's operational context alongside the SBOM finding.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260717_0065"
down_revision = "20260715_0064"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sbom_vulnerability_findings",
        sa.Column("is_known_exploited", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index(
        "ix_sbom_vulnerability_findings_is_known_exploited",
        "sbom_vulnerability_findings",
        ["is_known_exploited"],
    )
    op.add_column("sbom_vulnerability_findings", sa.Column("kev_date_added", sa.DateTime(timezone=True), nullable=True))
    op.add_column("sbom_vulnerability_findings", sa.Column("kev_due_date", sa.DateTime(timezone=True), nullable=True))
    op.add_column("sbom_vulnerability_findings", sa.Column("kev_required_action", sa.Text(), nullable=True))
    op.add_column("sbom_vulnerability_findings", sa.Column("kev_known_ransomware_campaign_use", sa.String(length=20), nullable=True))
    op.add_column("sbom_vulnerability_findings", sa.Column("kev_fetched_at", sa.DateTime(timezone=True), nullable=True))
    op.alter_column("sbom_vulnerability_findings", "is_known_exploited", server_default=None)


def downgrade() -> None:
    op.drop_column("sbom_vulnerability_findings", "kev_fetched_at")
    op.drop_column("sbom_vulnerability_findings", "kev_known_ransomware_campaign_use")
    op.drop_column("sbom_vulnerability_findings", "kev_required_action")
    op.drop_column("sbom_vulnerability_findings", "kev_due_date")
    op.drop_column("sbom_vulnerability_findings", "kev_date_added")
    op.drop_index("ix_sbom_vulnerability_findings_is_known_exploited", table_name="sbom_vulnerability_findings")
    op.drop_column("sbom_vulnerability_findings", "is_known_exploited")
