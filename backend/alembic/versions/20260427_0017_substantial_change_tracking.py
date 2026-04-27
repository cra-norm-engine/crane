"""
Add substantial change tracking tables.

Creates three new tables:
  - changes: records modifications made to product versions
  - substantial_modification_assessments: CRA assessment per change
  - change_compliance_actions: individual compliance tasks for substantial changes

Revision ID: 20260427_0017
Revises: 20260426_0016
Create Date: 2026-04-27
"""

from alembic import op
import sqlalchemy as sa

revision = "20260427_0017"
down_revision = "20260426_0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # changes
    # Records each modification made to a product version with workflow status.
    # -------------------------------------------------------------------------
    op.create_table(
        "changes",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),

        # Foreign keys
        sa.Column(
            "product_version_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("product_releases.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "initiator_user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "assessor_user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),

        # Change details
        sa.Column("change_type", sa.String(30), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("change_date", sa.Date, nullable=False),

        # Workflow state
        sa.Column("status", sa.String(30), nullable=False, server_default="draft"),
        sa.Column("submitted_at", sa.Date, nullable=True),
        sa.Column("assessed_at", sa.Date, nullable=True),
        sa.Column("closed_at", sa.Date, nullable=True),
    )
    op.create_index("ix_changes_product_version_id", "changes", ["product_version_id"])
    op.create_index("ix_changes_status", "changes", ["status"])
    op.create_index("ix_changes_change_type", "changes", ["change_type"])
    op.create_index("ix_changes_initiator_user_id", "changes", ["initiator_user_id"])

    # -------------------------------------------------------------------------
    # substantial_modification_assessments
    # One-to-one with a change; records the four CRA criteria and the decision.
    # -------------------------------------------------------------------------
    op.create_table(
        "substantial_modification_assessments",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),

        sa.Column(
            "change_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("changes.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "assessor_user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),

        # The four CRA criteria (any True → is_substantial = True)
        sa.Column("alters_intended_use", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("increases_cybersecurity_risk", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("changes_hazard_nature", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("expands_attack_surface", sa.Boolean, nullable=False, server_default="false"),

        # Outcome
        sa.Column("is_substantial", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("reasoning", sa.Text, nullable=False),
        sa.Column("decision_date", sa.Date, nullable=False),

        sa.UniqueConstraint("change_id", name="uq_assessment_change"),
    )
    op.create_index(
        "ix_substantial_modification_assessments_change_id",
        "substantial_modification_assessments",
        ["change_id"],
    )
    op.create_index(
        "ix_substantial_modification_assessments_is_substantial",
        "substantial_modification_assessments",
        ["is_substantial"],
    )

    # -------------------------------------------------------------------------
    # change_compliance_actions
    # Individual tasks that must be completed when a change is substantial.
    # -------------------------------------------------------------------------
    op.create_table(
        "change_compliance_actions",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),

        sa.Column(
            "assessment_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("substantial_modification_assessments.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "completed_by_user_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),

        sa.Column("action_type", sa.String(60), nullable=False),
        sa.Column("action_status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("due_date", sa.Date, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
    )
    op.create_index(
        "ix_change_compliance_actions_assessment_id",
        "change_compliance_actions",
        ["assessment_id"],
    )
    op.create_index(
        "ix_change_compliance_actions_action_status",
        "change_compliance_actions",
        ["action_status"],
    )


def downgrade() -> None:
    # Drop in reverse order of creation to respect foreign key constraints
    op.drop_table("change_compliance_actions")
    op.drop_table("substantial_modification_assessments")
    op.drop_table("changes")
