"""add instance-wide vulnerability scanning setting"""

import sqlalchemy as sa
from alembic import op

revision = "20260910_0082"
down_revision = "20260904_0081"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "system_settings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("vulnerability_scanning_enabled", sa.Boolean(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("system_settings")
