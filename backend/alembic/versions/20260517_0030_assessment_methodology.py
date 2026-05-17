"""Add methodology and template_answers to substantial_modification_assessments.

Allows storing the assessment methodology (STRIDE, TARA, custom) and structured
answers per methodology alongside the four CRA criteria.

Revision ID: 20260517_0030
Revises: 20260517_0029
Create Date: 2026-05-17
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "20260517_0030"
down_revision = "20260517_0029"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "substantial_modification_assessments",
        sa.Column("methodology", sa.String(50), nullable=True),
    )
    op.add_column(
        "substantial_modification_assessments",
        sa.Column("template_answers", JSONB(), nullable=True),
    )
    op.create_index(
        "ix_substantial_modification_assessments_methodology",
        "substantial_modification_assessments",
        ["methodology"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_substantial_modification_assessments_methodology",
        table_name="substantial_modification_assessments",
    )
    op.drop_column("substantial_modification_assessments", "template_answers")
    op.drop_column("substantial_modification_assessments", "methodology")
