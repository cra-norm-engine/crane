"""Add is_embedded_product, hw/sw versions on releases, and release↔RPE join table.

Gap 2: Products that combine hardware and firmware/software (e.g. embedded IoT devices)
need separate hardware_version and software_version fields on each release so each
HW+SW combination can be documented for CRA compliance.

Gap 1: Remote processing elements are defined at product level; each release must
explicitly confirm which elements apply to that release via a M2M join table.

Revision ID: 20260529_0044
Revises: 20260529_0043
Create Date: 2026-05-29
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260529_0044"
down_revision = "20260529_0043"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Gap 2 — mark a product as an embedded (hardware+software) product so that
    # per-release hardware_version and software_version fields are surfaced.
    op.add_column(
        "products",
        sa.Column("is_embedded_product", sa.Boolean(), nullable=False, server_default="false"),
    )

    # Gap 2 — per-release hardware and software version strings for embedded products.
    # Both nullable so they are invisible for pure-software products.
    op.add_column(
        "product_releases",
        sa.Column("hardware_version", sa.String(150), nullable=True),
    )
    op.add_column(
        "product_releases",
        sa.Column("software_version", sa.String(150), nullable=True),
    )

    # Gap 1 — M2M join table: which remote processing elements are in scope for
    # a given release. CASCADE deletes keep the join table tidy when either side
    # is removed.
    op.create_table(
        "release_remote_processing_elements",
        sa.Column(
            "release_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("product_releases.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "rpe_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("remote_processing_elements.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("release_remote_processing_elements")
    op.drop_column("product_releases", "software_version")
    op.drop_column("product_releases", "hardware_version")
    op.drop_column("products", "is_embedded_product")
