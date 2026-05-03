"""Add must_change_password to users table.

Local (non-LDAP) users created by an admin get a temporary password;
this flag forces them to change it on first login.  Existing users are
left with must_change_password=False so they are not interrupted.

Revision ID: 20260503_0020
Revises: 20260501_0019
Create Date: 2026-05-03
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260503_0020"
down_revision = "20260501_0019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "must_change_password",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "must_change_password")
