"""add artifact library and release gate workflow

Revision ID: 20260406_0008
Revises: 20260405_0007
Create Date: 2026-04-06 00:00:00
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260406_0008"
down_revision = "20260405_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    artifact_source_type = postgresql.ENUM(
        "upload",
        "external_link",
        name="artifactsourcetype",
        create_type=False,
    )
    artifact_review_decision = postgresql.ENUM(
        "pending_review",
        "accepted",
        "rejected",
        "needs_update",
        "waived",
        name="artifactreviewdecision",
        create_type=False,
    )
    release_gate_workflow_status = postgresql.ENUM(
        "draft",
        "in_review",
        "approved",
        "blocked",
        name="releasegateworkflowstatus",
        create_type=False,
    )
    release_gate_item_code = postgresql.ENUM(
        "technical_documentation",
        "risk_assessment",
        "sbom",
        "test_report",
        "declaration_of_conformity",
        "annex_mapping",
        name="releasegateitemcode",
        create_type=False,
    )

    artifact_source_type.create(bind, checkfirst=True)
    artifact_review_decision.create(bind, checkfirst=True)
    release_gate_workflow_status.create(bind, checkfirst=True)
    release_gate_item_code.create(bind, checkfirst=True)

    op.create_table(
        "artifacts",
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("artifact_type", postgresql.ENUM(name="evidencetype", create_type=False), nullable=False),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_artifacts_title", "artifacts", ["title"], unique=False)
    op.create_index("ix_artifacts_artifact_type", "artifacts", ["artifact_type"], unique=False)
    op.create_index("ix_artifacts_created_by_user_id", "artifacts", ["created_by_user_id"], unique=False)

    op.create_table(
        "artifact_revisions",
        sa.Column("artifact_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("artifacts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("source_type", artifact_source_type, nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=True),
        sa.Column("content_type", sa.String(length=255), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("sha256", sa.String(length=64), nullable=True),
        sa.Column("storage_path", sa.String(length=1000), nullable=True),
        sa.Column("external_url", sa.String(length=2048), nullable=True),
        sa.Column("change_summary", sa.Text(), nullable=True),
        sa.Column("uploaded_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("artifact_id", "revision_number", name="uq_artifact_revisions_artifact_revision"),
    )
    op.create_index("ix_artifact_revisions_artifact_id", "artifact_revisions", ["artifact_id"], unique=False)
    op.create_index("ix_artifact_revisions_sha256", "artifact_revisions", ["sha256"], unique=False)
    op.create_index("ix_artifact_revisions_uploaded_by_user_id", "artifact_revisions", ["uploaded_by_user_id"], unique=False)

    op.create_table(
        "artifact_product_links",
        sa.Column("artifact_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("artifacts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("artifact_id", "product_id", name="uq_artifact_product_links_artifact_product"),
    )
    op.create_index("ix_artifact_product_links_artifact_id", "artifact_product_links", ["artifact_id"], unique=False)
    op.create_index("ix_artifact_product_links_product_id", "artifact_product_links", ["product_id"], unique=False)

    op.create_table(
        "release_gates",
        sa.Column("product_release_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("product_releases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", release_gate_workflow_status, nullable=False, server_default="draft"),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("submitted_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_release_id", name="uq_release_gates_product_release"),
    )
    op.create_index("ix_release_gates_product_release_id", "release_gates", ["product_release_id"], unique=False)
    op.create_index("ix_release_gates_status", "release_gates", ["status"], unique=False)
    op.create_index("ix_release_gates_submitted_by_user_id", "release_gates", ["submitted_by_user_id"], unique=False)
    op.create_index("ix_release_gates_approved_by_user_id", "release_gates", ["approved_by_user_id"], unique=False)

    op.create_table(
        "release_gate_items",
        sa.Column("release_gate_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("release_gates.id", ondelete="CASCADE"), nullable=False),
        sa.Column("code", release_gate_item_code, nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_required", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", artifact_review_decision, nullable=False, server_default="pending_review"),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("release_gate_id", "code", name="uq_release_gate_items_gate_code"),
    )
    op.create_index("ix_release_gate_items_release_gate_id", "release_gate_items", ["release_gate_id"], unique=False)
    op.create_index("ix_release_gate_items_code", "release_gate_items", ["code"], unique=False)
    op.create_index("ix_release_gate_items_status", "release_gate_items", ["status"], unique=False)

    op.create_table(
        "release_gate_evidence_links",
        sa.Column("release_gate_item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("release_gate_items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("artifact_revision_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("artifact_revisions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("linked_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("decision", artifact_review_decision, nullable=False, server_default="pending_review"),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("reviewed_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("release_gate_item_id", "artifact_revision_id", name="uq_release_gate_evidence_item_revision"),
    )
    op.create_index("ix_release_gate_evidence_links_release_gate_item_id", "release_gate_evidence_links", ["release_gate_item_id"], unique=False)
    op.create_index("ix_release_gate_evidence_links_artifact_revision_id", "release_gate_evidence_links", ["artifact_revision_id"], unique=False)
    op.create_index("ix_release_gate_evidence_links_linked_by_user_id", "release_gate_evidence_links", ["linked_by_user_id"], unique=False)
    op.create_index("ix_release_gate_evidence_links_decision", "release_gate_evidence_links", ["decision"], unique=False)
    op.create_index("ix_release_gate_evidence_links_reviewed_by_user_id", "release_gate_evidence_links", ["reviewed_by_user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_release_gate_evidence_links_reviewed_by_user_id", table_name="release_gate_evidence_links")
    op.drop_index("ix_release_gate_evidence_links_decision", table_name="release_gate_evidence_links")
    op.drop_index("ix_release_gate_evidence_links_linked_by_user_id", table_name="release_gate_evidence_links")
    op.drop_index("ix_release_gate_evidence_links_artifact_revision_id", table_name="release_gate_evidence_links")
    op.drop_index("ix_release_gate_evidence_links_release_gate_item_id", table_name="release_gate_evidence_links")
    op.drop_table("release_gate_evidence_links")

    op.drop_index("ix_release_gate_items_status", table_name="release_gate_items")
    op.drop_index("ix_release_gate_items_code", table_name="release_gate_items")
    op.drop_index("ix_release_gate_items_release_gate_id", table_name="release_gate_items")
    op.drop_table("release_gate_items")

    op.drop_index("ix_release_gates_approved_by_user_id", table_name="release_gates")
    op.drop_index("ix_release_gates_submitted_by_user_id", table_name="release_gates")
    op.drop_index("ix_release_gates_status", table_name="release_gates")
    op.drop_index("ix_release_gates_product_release_id", table_name="release_gates")
    op.drop_table("release_gates")

    op.drop_index("ix_artifact_product_links_product_id", table_name="artifact_product_links")
    op.drop_index("ix_artifact_product_links_artifact_id", table_name="artifact_product_links")
    op.drop_table("artifact_product_links")

    op.drop_index("ix_artifact_revisions_uploaded_by_user_id", table_name="artifact_revisions")
    op.drop_index("ix_artifact_revisions_sha256", table_name="artifact_revisions")
    op.drop_index("ix_artifact_revisions_artifact_id", table_name="artifact_revisions")
    op.drop_table("artifact_revisions")

    op.drop_index("ix_artifacts_created_by_user_id", table_name="artifacts")
    op.drop_index("ix_artifacts_artifact_type", table_name="artifacts")
    op.drop_index("ix_artifacts_title", table_name="artifacts")
    op.drop_table("artifacts")

    postgresql.ENUM(name="releasegateitemcode").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="releasegateworkflowstatus").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="artifactreviewdecision").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="artifactsourcetype").drop(op.get_bind(), checkfirst=True)
