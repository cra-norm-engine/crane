"""add sources_json to sbom_vulnerability_findings

Records which scanner(s) detected each CVE finding (osv, trivy, nvd).

Revision ID: 20260524_0035
Revises: 20260523_0034
Create Date: 2026-05-24 00:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260524_0035"
down_revision = "20260523_0034"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # server_default writes '["osv"]' into every existing row at ALTER time.
    op.add_column(
        "sbom_vulnerability_findings",
        sa.Column(
            "sources_json",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default='["osv"]',
        ),
    )


def downgrade() -> None:
    op.drop_column("sbom_vulnerability_findings", "sources_json")
