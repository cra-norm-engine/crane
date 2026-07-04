"""Enrich products with scope provenance, conformity route, type & system metadata.

Combines the additive enrichment for Phases 2-4 of the product-inventory
enrichment:

* Phase 2 — out-of-scope decision provenance: out_of_scope_justification,
  scope_decided_by_user_id (FK users SET NULL), scope_decided_at,
  scope_decision_signature.
* Phase 3 — typed CRA product classification (product_type_class enum) and a
  product-level conformity_route (reuses the existing conformityroute enum).
* Phase 4 — additive JSONB metadata: system_profile_json, tailor_made_terms_json.

All columns are nullable or carry server_defaults, so this migration is safe on
populated tables and introduces no downstream breakage (scope_status and
current_classification are untouched).

Revision ID: 20260628_0060
Revises: 20260628_0059
Create Date: 2026-06-28
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260628_0060"
down_revision = "20260628_0059"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    # --- Phase 3: ProductType enum + typed classification column ---
    product_type_enum = postgresql.ENUM(
        "type1_software",
        "type2_hardware_with_digital",
        "undecided",
        name="producttype",
        create_type=False,
    )
    product_type_enum.create(bind, checkfirst=True)

    op.add_column(
        "products",
        sa.Column(
            "product_type_class",
            product_type_enum,
            nullable=False,
            server_default="undecided",
        ),
    )
    op.create_index("ix_products_product_type_class", "products", ["product_type_class"])

    # Backfill the typed classification from the existing is_embedded_product flag:
    # embedded products are hardware-with-digital (TYPE2), the rest software (TYPE1).
    op.execute(
        "UPDATE products SET product_type_class = 'type2_hardware_with_digital' "
        "WHERE is_embedded_product = true"
    )
    op.execute(
        "UPDATE products SET product_type_class = 'type1_software' "
        "WHERE is_embedded_product = false"
    )

    # --- Phase 3: product-level conformity route (reuse existing enum) ---
    conformity_route_enum = postgresql.ENUM(
        "self_assessment",
        "third_party_assessment",
        "not_applicable",
        "undecided",
        name="conformityroute",
        create_type=False,
    )
    op.add_column(
        "products",
        sa.Column(
            "conformity_route",
            conformity_route_enum,
            nullable=False,
            server_default="undecided",
        ),
    )
    op.create_index("ix_products_conformity_route", "products", ["conformity_route"])

    # --- Phase 2: out-of-scope decision provenance ---
    op.add_column("products", sa.Column("out_of_scope_justification", sa.Text(), nullable=True))
    op.add_column(
        "products",
        sa.Column("scope_decided_by_user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_products_scope_decided_by_user_id",
        "products",
        "users",
        ["scope_decided_by_user_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.add_column(
        "products",
        sa.Column("scope_decided_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "products",
        sa.Column("scope_decision_signature", sa.String(length=255), nullable=True),
    )

    # --- Phase 4: additive JSONB metadata ---
    op.add_column("products", sa.Column("system_profile_json", postgresql.JSONB(), nullable=True))
    op.add_column("products", sa.Column("tailor_made_terms_json", postgresql.JSONB(), nullable=True))


def downgrade() -> None:
    op.drop_column("products", "tailor_made_terms_json")
    op.drop_column("products", "system_profile_json")

    op.drop_column("products", "scope_decision_signature")
    op.drop_column("products", "scope_decided_at")
    op.drop_constraint("fk_products_scope_decided_by_user_id", "products", type_="foreignkey")
    op.drop_column("products", "scope_decided_by_user_id")
    op.drop_column("products", "out_of_scope_justification")

    op.drop_index("ix_products_conformity_route", table_name="products")
    op.drop_column("products", "conformity_route")

    op.drop_index("ix_products_product_type_class", table_name="products")
    op.drop_column("products", "product_type_class")
    postgresql.ENUM(name="producttype").drop(op.get_bind(), checkfirst=True)
