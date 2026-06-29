"""Add release requirement assessment approval + append-only snapshots.

Introduces a release-level "requirement assessment" that can be formally
approved (freezing the Annex I matrix and gating the release workflow), plus an
immutable snapshot table that records each approval (append-only history).

Revision ID: 20260627_0057
Revises: 20260619_0056
Create Date: 2026-06-27
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import JSONB

revision = "20260627_0057"
down_revision = "20260619_0056"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    requirement_assessment_status = postgresql.ENUM(
        "draft",
        "approved",
        name="requirementassessmentstatus",
        create_type=False,
    )
    requirement_assessment_status.create(bind, checkfirst=True)

    op.create_table(
        "release_requirement_assessments",
        sa.Column("product_release_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("product_releases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", requirement_assessment_status, nullable=False, server_default="draft"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by_user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_release_id", name="uq_release_requirement_assessments_release"),
    )
    op.create_index("ix_release_requirement_assessments_product_release_id",
                    "release_requirement_assessments", ["product_release_id"])
    op.create_index("ix_release_requirement_assessments_status",
                    "release_requirement_assessments", ["status"])

    op.create_table(
        "release_requirement_assessment_snapshots",
        sa.Column("release_requirement_assessment_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("release_requirement_assessments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("approved_by_user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("snapshot_json", JSONB(), nullable=False),
        sa.Column("content_sha256", sa.String(length=64), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("release_requirement_assessment_id", "version",
                            name="uq_requirement_assessment_snapshots_version"),
    )
    op.create_index("ix_release_requirement_assessment_snapshots_assessment_id",
                    "release_requirement_assessment_snapshots",
                    ["release_requirement_assessment_id"])


def downgrade() -> None:
    op.drop_index("ix_release_requirement_assessment_snapshots_assessment_id",
                  table_name="release_requirement_assessment_snapshots")
    op.drop_table("release_requirement_assessment_snapshots")
    op.drop_index("ix_release_requirement_assessments_status",
                  table_name="release_requirement_assessments")
    op.drop_index("ix_release_requirement_assessments_product_release_id",
                  table_name="release_requirement_assessments")
    op.drop_table("release_requirement_assessments")

    bind = op.get_bind()
    postgresql.ENUM(name="requirementassessmentstatus").drop(bind, checkfirst=True)
