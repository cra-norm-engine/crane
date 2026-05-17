"""Add snapshot_json to release_gates for compliance snapshot capture.

Stores a frozen JSON snapshot of all gate items and evidence at approval time,
enabling before/after comparisons and compliance audit trails.

Revision ID: 20260517_0032
Revises: 20260517_0031
Create Date: 2026-05-17
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "20260517_0032"
down_revision = "20260517_0031"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "release_gates",
        sa.Column("snapshot_json", JSONB(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("release_gates", "snapshot_json")
