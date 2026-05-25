"""requirement mappings and decisions per release

Revision ID: 20260525_0039
Revises: 20260524_0038_add_substantiality_analysis_to_releases
Create Date: 2026-05-25

Changes:
- RequirementMapping: add product_release_id (NOT NULL, FK → product_releases)
- ProductRequirementDecision: replace product_id with product_release_id,
  update unique constraint to (product_release_id, annex_requirement_id)

Existing rows are deleted because they have no release context.
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "20260525_0039"
down_revision = "20260524_0038"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── requirement_mappings: add product_release_id ──────────────────────────
    # Delete existing rows — they carry no release context and cannot be migrated.
    op.execute("DELETE FROM requirement_mappings")

    op.add_column(
        "requirement_mappings",
        sa.Column(
            "product_release_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_requirement_mappings_product_release_id",
        "requirement_mappings",
        ["product_release_id"],
    )
    op.create_foreign_key(
        "fk_requirement_mappings_product_release_id",
        "requirement_mappings",
        "product_releases",
        ["product_release_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # ── product_requirement_decisions: swap product_id → product_release_id ───
    op.execute("DELETE FROM product_requirement_decisions")

    op.drop_constraint(
        "uq_product_requirement_decisions_product_requirement",
        "product_requirement_decisions",
        type_="unique",
    )
    op.drop_index(
        "ix_product_requirement_decisions_product_id",
        table_name="product_requirement_decisions",
    )
    op.drop_constraint(
        "product_requirement_decisions_product_id_fkey",
        "product_requirement_decisions",
        type_="foreignkey",
    )
    op.drop_column("product_requirement_decisions", "product_id")

    op.add_column(
        "product_requirement_decisions",
        sa.Column(
            "product_release_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_product_requirement_decisions_product_release_id",
        "product_requirement_decisions",
        ["product_release_id"],
    )
    op.create_foreign_key(
        "fk_product_requirement_decisions_product_release_id",
        "product_requirement_decisions",
        "product_releases",
        ["product_release_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_unique_constraint(
        "uq_product_requirement_decisions_release_requirement",
        "product_requirement_decisions",
        ["product_release_id", "annex_requirement_id"],
    )


def downgrade() -> None:
    # ── product_requirement_decisions: revert to product_id ──────────────────
    op.execute("DELETE FROM product_requirement_decisions")

    op.drop_constraint(
        "uq_product_requirement_decisions_release_requirement",
        "product_requirement_decisions",
        type_="unique",
    )
    op.drop_index(
        "ix_product_requirement_decisions_product_release_id",
        table_name="product_requirement_decisions",
    )
    op.drop_constraint(
        "fk_product_requirement_decisions_product_release_id",
        "product_requirement_decisions",
        type_="foreignkey",
    )
    op.drop_column("product_requirement_decisions", "product_release_id")

    op.add_column(
        "product_requirement_decisions",
        sa.Column(
            "product_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_product_requirement_decisions_product_id",
        "product_requirement_decisions",
        ["product_id"],
    )
    op.create_foreign_key(
        "product_requirement_decisions_product_id_fkey",
        "product_requirement_decisions",
        "products",
        ["product_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_unique_constraint(
        "uq_product_requirement_decisions_product_requirement",
        "product_requirement_decisions",
        ["product_id", "annex_requirement_id"],
    )

    # ── requirement_mappings: drop product_release_id ────────────────────────
    op.execute("DELETE FROM requirement_mappings")

    op.drop_index(
        "ix_requirement_mappings_product_release_id",
        table_name="requirement_mappings",
    )
    op.drop_constraint(
        "fk_requirement_mappings_product_release_id",
        "requirement_mappings",
        type_="foreignkey",
    )
    op.drop_column("requirement_mappings", "product_release_id")
