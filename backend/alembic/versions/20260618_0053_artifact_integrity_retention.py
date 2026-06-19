"""Add artifact integrity-verification and retention / legal-hold columns.

Document assurance (CRA Art. 31): per-revision integrity status + last-verified
timestamp (the file is re-hashed against the stored SHA-256), and per-artifact
retention deadline + legal-hold so evidence cannot be deleted prematurely.

Revision ID: 20260618_0053
Revises: 20260614_0052
Create Date: 2026-06-18
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260618_0053"
down_revision = "20260614_0052"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Retention & legal hold on the artifact (document) level.
    op.add_column("artifacts", sa.Column("retention_until", sa.Date(), nullable=True))
    op.add_column(
        "artifacts",
        sa.Column("legal_hold", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("artifacts", sa.Column("legal_hold_reason", sa.Text(), nullable=True))
    # Drop the server_default now that existing rows are backfilled to False.
    op.alter_column("artifacts", "legal_hold", server_default=None)

    # Integrity verification on the revision (file) level.
    op.add_column("artifact_revisions", sa.Column("integrity_status", sa.String(length=20), nullable=True))
    op.add_column(
        "artifact_revisions",
        sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("artifact_revisions", "last_verified_at")
    op.drop_column("artifact_revisions", "integrity_status")
    op.drop_column("artifacts", "legal_hold_reason")
    op.drop_column("artifacts", "legal_hold")
    op.drop_column("artifacts", "retention_until")
