"""add CRANE system update policy

Revision ID: 20260912_0085
Revises: 20260911_0084
"""

import sqlalchemy as sa
from alembic import op

revision = "20260912_0085"
down_revision = "20260911_0084"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "system_settings",
        sa.Column("update_policy", sa.String(length=30), nullable=False, server_default="manual"),
    )
    op.add_column(
        "system_settings",
        sa.Column("update_channel", sa.String(length=20), nullable=False, server_default="stable"),
    )
    op.add_column(
        "system_settings",
        sa.Column("update_maintenance_day", sa.Integer(), nullable=False, server_default="6"),
    )
    op.add_column(
        "system_settings",
        sa.Column("update_maintenance_hour_utc", sa.Integer(), nullable=False, server_default="2"),
    )
    op.add_column(
        "system_settings",
        sa.Column("update_postponed_until", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("system_settings", "update_postponed_until")
    op.drop_column("system_settings", "update_maintenance_hour_utc")
    op.drop_column("system_settings", "update_maintenance_day")
    op.drop_column("system_settings", "update_channel")
    op.drop_column("system_settings", "update_policy")
