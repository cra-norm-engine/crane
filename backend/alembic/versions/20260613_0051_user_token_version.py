"""Add token_version to users for refresh-token invalidation.

Incrementing a user's token_version immediately invalidates all of that user's
outstanding access and refresh tokens (used on password change and refresh-token
reuse/theft detection). Existing users start at 0 so they are not interrupted.

Revision ID: 20260613_0051
Revises: 20260609_0050
Create Date: 2026-06-13
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260613_0051"
down_revision = "20260609_0050"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "token_version",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "token_version")
