"""security update CRA req7 fields: severity, integrity_info, is_security_only, update_channels

Revision ID: 20260425_0013
Revises: 20260425_0012
Create Date: 2026-04-25 10:00:00
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260425_0013"
down_revision = "20260425_0012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("security_updates", sa.Column("severity", sa.String(), nullable=True))
    op.add_column("security_updates", sa.Column("is_security_only", sa.Boolean(), nullable=False, server_default="true"))
    op.add_column("security_updates", sa.Column("integrity_info", sa.Text(), nullable=True))
    op.add_column("security_updates", sa.Column("update_channels_json", sa.dialects.postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")))
    op.create_index("ix_security_updates_severity", "security_updates", ["severity"])


def downgrade() -> None:
    op.drop_index("ix_security_updates_severity", "security_updates")
    op.drop_column("security_updates", "update_channels_json")
    op.drop_column("security_updates", "integrity_info")
    op.drop_column("security_updates", "is_security_only")
    op.drop_column("security_updates", "severity")
