"""requirement mapping artifact links

Revision ID: 20260412_0009
Revises: 20260406_0008
Create Date: 2026-04-12 00:00:00
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260412_0009"
down_revision = "20260406_0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "requirement_mapping_artifact_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "requirement_mapping_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("requirement_mappings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "artifact_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("artifacts.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "requirement_mapping_id",
            "artifact_id",
            name="uq_requirement_mapping_artifact_link",
        ),
    )
    op.create_index(
        "ix_requirement_mapping_artifact_links_requirement_mapping_id",
        "requirement_mapping_artifact_links",
        ["requirement_mapping_id"],
        unique=False,
    )
    op.create_index(
        "ix_requirement_mapping_artifact_links_artifact_id",
        "requirement_mapping_artifact_links",
        ["artifact_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_requirement_mapping_artifact_links_artifact_id",
        table_name="requirement_mapping_artifact_links",
    )
    op.drop_index(
        "ix_requirement_mapping_artifact_links_requirement_mapping_id",
        table_name="requirement_mapping_artifact_links",
    )
    op.drop_table("requirement_mapping_artifact_links")
