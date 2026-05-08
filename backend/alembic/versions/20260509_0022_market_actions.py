"""Market actions table — CRA Art. 35 recalls and withdrawals (FR38, FR39).

Adds the market_actions table to track the full workflow for product recalls
and withdrawals, including authority notification and closure.

Revision ID: 20260509_0022
Revises: 20260503_0021
Create Date: 2026-05-09
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260509_0022"
down_revision = "20260503_0021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "market_actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_release_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, server_default="draft"),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("affected_scope", sa.Text(), nullable=True),
        sa.Column("corrective_action", sa.Text(), nullable=True),
        sa.Column("authority_reference_number", sa.String(255), nullable=True),
        sa.Column(
            "authority_notified_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column("user_notice_text", sa.Text(), nullable=True),
        sa.Column("internal_notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["product_release_id"],
            ["product_releases.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_market_actions_product_release_id",
        "market_actions",
        ["product_release_id"],
    )
    op.create_index(
        "ix_market_actions_status",
        "market_actions",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index("ix_market_actions_status", table_name="market_actions")
    op.drop_index("ix_market_actions_product_release_id", table_name="market_actions")
    op.drop_table("market_actions")
