"""Add CRA Art. 3(2) classification fields to remote_processing_elements.

Revision ID: 20260529_0043
Revises: 20260527_0042
Create Date: 2026-05-29
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260529_0043"
down_revision = "20260527_0042"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create the two new enum types
    op.execute(
        "CREATE TYPE remoteprocessingelementtype AS ENUM "
        "('saas', 'internal_cloud', 'external_api', 'backend_service', 'data_processing', 'firmware_update', 'other')"
    )
    op.execute(
        "CREATE TYPE remoteprocessingclassification AS ENUM "
        "('not_assessed', 'cra_art_3_2_in_scope', 'third_party_component', 'out_of_scope', 'requires_legal_assessment')"
    )

    # Add assessment columns
    op.add_column(
        "remote_processing_elements",
        sa.Column(
            "element_type",
            postgresql.ENUM(name="remoteprocessingelementtype", create_type=False),
            nullable=True,
        ),
    )
    op.add_column(
        "remote_processing_elements",
        sa.Column("has_downloadable_component", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "remote_processing_elements",
        sa.Column("is_browser_only_access", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "remote_processing_elements",
        sa.Column("is_essential_to_core_function", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "remote_processing_elements",
        sa.Column("is_manufacturer_owned", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "remote_processing_elements",
        sa.Column(
            "classification",
            postgresql.ENUM(name="remoteprocessingclassification", create_type=False),
            nullable=False,
            server_default="not_assessed",
        ),
    )
    op.add_column(
        "remote_processing_elements",
        sa.Column("classification_rationale", sa.Text(), nullable=True),
    )
    op.add_column(
        "remote_processing_elements",
        sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "remote_processing_elements",
        sa.Column(
            "assessed_by_user_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_rpe_assessed_by_user_id",
        "remote_processing_elements",
        "users",
        ["assessed_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_remote_processing_elements_classification",
        "remote_processing_elements",
        ["classification"],
    )


def downgrade() -> None:
    op.drop_index("ix_remote_processing_elements_classification", table_name="remote_processing_elements")
    op.drop_constraint("fk_rpe_assessed_by_user_id", "remote_processing_elements", type_="foreignkey")
    op.drop_column("remote_processing_elements", "assessed_by_user_id")
    op.drop_column("remote_processing_elements", "assessed_at")
    op.drop_column("remote_processing_elements", "classification_rationale")
    op.drop_column("remote_processing_elements", "classification")
    op.drop_column("remote_processing_elements", "is_manufacturer_owned")
    op.drop_column("remote_processing_elements", "is_essential_to_core_function")
    op.drop_column("remote_processing_elements", "is_browser_only_access")
    op.drop_column("remote_processing_elements", "has_downloadable_component")
    op.drop_column("remote_processing_elements", "element_type")
    op.execute("DROP TYPE remoteprocessingclassification")
    op.execute("DROP TYPE remoteprocessingelementtype")
