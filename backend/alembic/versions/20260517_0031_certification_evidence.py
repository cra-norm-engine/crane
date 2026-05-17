"""Add certification_record_artifact_links table for evidence attachment.

Allows linking artifact revisions to certification records as supporting evidence,
with full revision history and SHA-256 integrity verification.

Revision ID: 20260517_0031
Revises: 20260517_0030
Create Date: 2026-05-17
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260517_0031"
down_revision = "20260517_0030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "certification_record_artifact_links",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("certification_record_id", sa.UUID(), nullable=False),
        sa.Column("artifact_revision_id", sa.UUID(), nullable=False),
        sa.Column("linked_by_user_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["certification_record_id"],
            ["certification_records.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["artifact_revision_id"],
            ["artifact_revisions.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["linked_by_user_id"],
            ["users.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "certification_record_id",
            "artifact_revision_id",
            name="uq_certification_artifact_revision",
        ),
    )
    op.create_index(
        "ix_certification_record_artifact_links_certification_record_id",
        "certification_record_artifact_links",
        ["certification_record_id"],
    )
    op.create_index(
        "ix_certification_record_artifact_links_artifact_revision_id",
        "certification_record_artifact_links",
        ["artifact_revision_id"],
    )
    op.create_index(
        "ix_certification_record_artifact_links_linked_by_user_id",
        "certification_record_artifact_links",
        ["linked_by_user_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_certification_record_artifact_links_linked_by_user_id",
        table_name="certification_record_artifact_links",
    )
    op.drop_index(
        "ix_certification_record_artifact_links_artifact_revision_id",
        table_name="certification_record_artifact_links",
    )
    op.drop_index(
        "ix_certification_record_artifact_links_certification_record_id",
        table_name="certification_record_artifact_links",
    )
    op.drop_table("certification_record_artifact_links")
