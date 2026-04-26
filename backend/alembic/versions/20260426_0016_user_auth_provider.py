"""Add auth_provider column to users table

Revision ID: 20260426_0016
Revises: 20260426_0015
Create Date: 2026-04-26
"""

from alembic import op
import sqlalchemy as sa

revision = "20260426_0016"
down_revision = "20260426_0015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "auth_provider",
            sa.String(20),
            nullable=False,
            server_default="local",
        ),
    )
    op.create_index("ix_users_auth_provider", "users", ["auth_provider"])


def downgrade() -> None:
    op.drop_index("ix_users_auth_provider", table_name="users")
    op.drop_column("users", "auth_provider")
