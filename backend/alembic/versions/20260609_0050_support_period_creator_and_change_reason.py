"""support period: add created_by_user_id and change_reason

Revision ID: 20260609_0050
Revises: 20260609_0049
Create Date: 2026-06-09 00:00:00

Adds two fields to support_period_records:
  - created_by_user_id: which user created / versioned this record
  - change_reason: required justification when a support period is updated
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "20260609_0050"
down_revision = "20260609_0049"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "support_period_records",
        sa.Column(
            "created_by_user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_support_period_records_created_by_user_id",
        "support_period_records",
        ["created_by_user_id"],
    )
    op.add_column(
        "support_period_records",
        sa.Column("change_reason", sa.Text, nullable=True),
    )


def downgrade() -> None:
    op.drop_index(
        "ix_support_period_records_created_by_user_id",
        table_name="support_period_records",
    )
    op.drop_column("support_period_records", "created_by_user_id")
    op.drop_column("support_period_records", "change_reason")
