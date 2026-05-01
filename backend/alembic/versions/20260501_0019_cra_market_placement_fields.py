"""Add CRA market placement fields across products, releases, and support periods.

Implements all gaps identified in the CRA guidance (Ares(2026)2319816) gap analysis:

  Gap 1 — Support period must be per placed-version, not just per product.
           Adds nullable product_release_id FK to support_period_records.

  Gap 2 — Non-substantial updates must record which "base" release they derive from
           so the original placement date lineage is preserved.
           Adds parent_release_id self-FK on product_releases.

  Gap 3 — "Placing on the market" is a distinct regulatory event separate from the
           internal actual_release_date. Adds placed_on_market_date column.
           Also adds placed_on_market as a new ReleaseStatus enum value.

  Gap 4 — Pre-CRA products (Article 69(2)) must be distinguishable.
           Adds is_pre_cra boolean and first_placed_on_market_date to products.

  Gap 5 — Article 13(10) consolidated support version must be flaggable.
           Adds is_consolidated_support_version boolean to product_releases.

Revision ID: 20260501_0019
Revises: 20260428_0018
Create Date: 2026-05-01
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# Alembic revision identifiers
revision = "20260501_0019"
down_revision = "20260428_0018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Gap 3: add the new enum value to the PostgreSQL releasestatus type ──────
    # ALTER TYPE ... ADD VALUE is outside any transaction in Postgres, so we
    # execute it directly.  The IF NOT EXISTS guard makes the migration idempotent.
    op.execute("ALTER TYPE releasestatus ADD VALUE IF NOT EXISTS 'placed_on_market'")

    # ── Gap 3: placed_on_market_date on product_releases ────────────────────────
    # The formal EU-market placement date (CRA Art. 3(20)), distinct from the
    # internal actual_release_date. NULL until the manufacturer confirms placement.
    op.add_column(
        "product_releases",
        sa.Column(
            "placed_on_market_date",
            sa.Date(),
            nullable=True,
            comment="Date this version was formally placed on the EU market (CRA Art. 3(20)). "
                    "Distinct from actual_release_date which tracks internal release timing.",
        ),
    )

    # ── Gap 2: parent_release_id on product_releases ─────────────────────────────
    # Self-referential FK: for non-substantial updates, points to the release
    # whose placement date this version inherits (CRA guidance §15, Example 2).
    # NULL for first-time placements and post-substantial-modification re-releases.
    op.add_column(
        "product_releases",
        sa.Column(
            "parent_release_id",
            sa.UUID(),
            nullable=True,
            comment="For non-substantial updates: FK to the release this version derives from. "
                    "Inherits that release's placed_on_market_date for compliance purposes.",
        ),
    )
    op.create_foreign_key(
        "fk_product_releases_parent_release",
        "product_releases",
        "product_releases",
        ["parent_release_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_product_releases_parent_release_id",
        "product_releases",
        ["parent_release_id"],
    )

    # ── Gap 5: is_consolidated_support_version on product_releases ───────────────
    # Article 13(10) flag: marks this release as the designated version whose
    # security updates cover all older versions in the product family.
    op.add_column(
        "product_releases",
        sa.Column(
            "is_consolidated_support_version",
            sa.Boolean(),
            nullable=False,
            server_default="false",
            comment="True when this release is the Art. 13(10) consolidated version "
                    "providing security update coverage for all prior versions.",
        ),
    )

    # ── Gap 4: is_pre_cra on products ───────────────────────────────────────────
    # Article 69(2) flag: True for products already on the EU market before CRA
    # full applicability (11 December 2024 / August 2026). These products have
    # distinct transition timelines and obligation start dates.
    op.add_column(
        "products",
        sa.Column(
            "is_pre_cra",
            sa.Boolean(),
            nullable=False,
            server_default="false",
            comment="True when the product was already on the EU market before CRA full "
                    "applicability. Triggers Article 69(2) transition provisions.",
        ),
    )

    # ── Gap 4: first_placed_on_market_date on products ───────────────────────────
    # The earliest known EU market placement date for this product line.
    # Critical for pre-CRA products and for calculating support period start
    # anchors when the exact release-level date is unavailable.
    op.add_column(
        "products",
        sa.Column(
            "first_placed_on_market_date",
            sa.Date(),
            nullable=True,
            comment="Earliest known EU market placement date for this product line. "
                    "Required for pre-CRA products under Article 69(2).",
        ),
    )

    # ── Gap 1: product_release_id on support_period_records ─────────────────────
    # Per-version support period linkage. If set, this record applies to a specific
    # placed release rather than the entire product (CRA guidance §117).
    # NULL is preserved for backwards compatibility with existing product-level records.
    op.add_column(
        "support_period_records",
        sa.Column(
            "product_release_id",
            sa.UUID(),
            nullable=True,
            comment="If set, this support period applies to a specific placed release "
                    "(CRA §117). NULL means product-level — used for legacy records.",
        ),
    )
    op.create_foreign_key(
        "fk_support_period_records_product_release",
        "support_period_records",
        "product_releases",
        ["product_release_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_support_period_records_product_release_id",
        "support_period_records",
        ["product_release_id"],
    )


def downgrade() -> None:
    # Remove support_period_records additions
    op.drop_index("ix_support_period_records_product_release_id", table_name="support_period_records")
    op.drop_constraint("fk_support_period_records_product_release", "support_period_records", type_="foreignkey")
    op.drop_column("support_period_records", "product_release_id")

    # Remove products additions
    op.drop_column("products", "first_placed_on_market_date")
    op.drop_column("products", "is_pre_cra")

    # Remove product_releases additions
    op.drop_column("product_releases", "is_consolidated_support_version")
    op.drop_index("ix_product_releases_parent_release_id", table_name="product_releases")
    op.drop_constraint("fk_product_releases_parent_release", "product_releases", type_="foreignkey")
    op.drop_column("product_releases", "parent_release_id")
    op.drop_column("product_releases", "placed_on_market_date")

    # Note: PostgreSQL does not support removing enum values. The placed_on_market
    # value will remain in the releasestatus type after downgrade. Manually recreate
    # the type without it if a complete rollback is required.
