"""Add user_preferences table for personal settings.

Stores per-user theme, timezone, date format, and default landing page surfaced
in the Settings hub. One row per user, created on first read/write.

Revision ID: 20260614_0052
Revises: 20260613_0051
Create Date: 2026-06-14
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "20260614_0052"
down_revision = "20260613_0051"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user_preferences",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("theme", sa.String(length=20), nullable=False, server_default="dark"),
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="UTC"),
        sa.Column(
            "date_format", sa.String(length=32), nullable=False, server_default="YYYY-MM-DD"
        ),
        sa.Column(
            "default_landing_page",
            sa.String(length=64),
            nullable=False,
            server_default="dashboard",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_unique_constraint(
        "uq_user_preferences_user_id", "user_preferences", ["user_id"]
    )
    op.create_index(
        "ix_user_preferences_user_id", "user_preferences", ["user_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_user_preferences_user_id", table_name="user_preferences")
    op.drop_constraint(
        "uq_user_preferences_user_id", "user_preferences", type_="unique"
    )
    op.drop_table("user_preferences")
