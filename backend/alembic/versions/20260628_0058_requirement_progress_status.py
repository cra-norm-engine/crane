"""Add per-requirement implementation progress status to the decision.

Introduces ``requirementprogressstatus`` (planned/implemented/validated) and an
``implementation_status`` column on ``product_requirement_decisions`` so each
requirement carries a single progress status per release (replacing the old
per-trace status as the driver of completeness).

Revision ID: 20260628_0058
Revises: 20260627_0057
Create Date: 2026-06-28
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260628_0058"
down_revision = "20260627_0057"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    progress_status = postgresql.ENUM(
        "planned",
        "implemented",
        "validated",
        name="requirementprogressstatus",
        create_type=False,
    )
    progress_status.create(bind, checkfirst=True)

    op.add_column(
        "product_requirement_decisions",
        sa.Column(
            "implementation_status",
            progress_status,
            nullable=False,
            server_default="planned",
        ),
    )
    op.create_index(
        "ix_product_requirement_decisions_implementation_status",
        "product_requirement_decisions",
        ["implementation_status"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_product_requirement_decisions_implementation_status",
        table_name="product_requirement_decisions",
    )
    op.drop_column("product_requirement_decisions", "implementation_status")

    bind = op.get_bind()
    postgresql.ENUM(name="requirementprogressstatus").drop(bind, checkfirst=True)
