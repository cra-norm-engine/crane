"""Add certification_scheme_label for custom scheme names

Revision ID: 20260426_0015
Revises: 20260426_0014
Create Date: 2026-04-26
"""

from alembic import op
import sqlalchemy as sa

revision = "20260426_0015"
down_revision = "20260426_0014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "certification_records",
        sa.Column("certification_scheme_label", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("certification_records", "certification_scheme_label")
