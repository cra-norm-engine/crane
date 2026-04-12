"""product requirement decisions

Revision ID: 20260412_0010
Revises: 20260412_0009
Create Date: 2026-04-12 00:10:00
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260412_0010"
down_revision = "20260412_0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    applicability = postgresql.ENUM(
        "undecided",
        "applicable",
        "not_applicable",
        name="requirementapplicabilitydecision",
        create_type=False,
    )
    applicability.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "product_requirement_decisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("annex_requirement_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("annex_requirements.id", ondelete="CASCADE"), nullable=False),
        sa.Column("applicability_decision", applicability, nullable=False, server_default="undecided"),
        sa.Column("rationale", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("product_id", "annex_requirement_id", name="uq_product_requirement_decisions_product_requirement"),
    )
    op.create_index("ix_product_requirement_decisions_product_id", "product_requirement_decisions", ["product_id"], unique=False)
    op.create_index("ix_product_requirement_decisions_annex_requirement_id", "product_requirement_decisions", ["annex_requirement_id"], unique=False)
    op.create_index("ix_product_requirement_decisions_applicability_decision", "product_requirement_decisions", ["applicability_decision"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_product_requirement_decisions_applicability_decision", table_name="product_requirement_decisions")
    op.drop_index("ix_product_requirement_decisions_annex_requirement_id", table_name="product_requirement_decisions")
    op.drop_index("ix_product_requirement_decisions_product_id", table_name="product_requirement_decisions")
    op.drop_table("product_requirement_decisions")
    postgresql.ENUM(name="requirementapplicabilitydecision").drop(op.get_bind(), checkfirst=True)
