"""release gate bundle hash and custom checklist items

Revision ID: 20260425_0012
Revises: 20260414_0011
Create Date: 2026-04-25 09:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260425_0012"
down_revision = "20260414_0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add bundle hash columns to release_gates
    op.add_column("release_gates", sa.Column("bundle_sha256", sa.String(64), nullable=True))
    op.add_column("release_gates", sa.Column("bundle_generated_at", sa.DateTime(timezone=True), nullable=True))

    # Make code nullable on release_gate_items to support custom (user-defined) items
    op.alter_column("release_gate_items", "code", existing_type=sa.String(), nullable=True)

    # Remove any existing technical_documentation gate items from open (non-approved) gates
    op.execute(
        """
        DELETE FROM release_gate_items
        WHERE code = 'technical_documentation'
          AND release_gate_id IN (
              SELECT id FROM release_gates WHERE status != 'approved'
          )
        """
    )


def downgrade() -> None:
    op.drop_column("release_gates", "bundle_sha256")
    op.drop_column("release_gates", "bundle_generated_at")
    op.alter_column("release_gate_items", "code", existing_type=sa.String(), nullable=False)
