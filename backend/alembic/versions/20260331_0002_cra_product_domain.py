"""cra product domain

Revision ID: 20260331_0002
Revises: 20260330_0001
Create Date: 2026-03-31 00:00:00
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260331_0002"
down_revision = "20260330_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    product_classification = postgresql.ENUM(
        "normal",
        "important_class_1",
        "important_class_2",
        "critical",
        name="productclassification",
        create_type=False,
    )
    conformity_route = postgresql.ENUM(
        "self_assessment",
        "third_party_assessment",
        "not_applicable",
        "undecided",
        name="conformityroute",
        create_type=False,
    )

    op.add_column("products", sa.Column("parent_product_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("products", sa.Column("manufacturer_name", sa.String(length=255), nullable=True))
    op.add_column("products", sa.Column("intended_use", sa.Text(), nullable=True))
    op.add_column("products", sa.Column("product_type", sa.String(length=150), nullable=True))
    op.add_column(
        "products",
        sa.Column(
            "current_classification",
            product_classification,
            nullable=False,
            server_default="normal",
        ),
    )
    op.add_column(
        "products",
        sa.Column("scope_status", sa.String(length=50), nullable=False, server_default="undecided"),
    )

    op.create_foreign_key(
        "fk_products_parent_product_id_products",
        "products",
        "products",
        ["parent_product_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_products_parent_product_id", "products", ["parent_product_id"], unique=False)
    op.create_index("ix_products_product_type", "products", ["product_type"], unique=False)
    op.create_index("ix_products_scope_status", "products", ["scope_status"], unique=False)

    op.execute("UPDATE products SET current_classification = classification")
    op.execute("UPDATE products SET manufacturer_name = 'Unknown manufacturer' WHERE manufacturer_name IS NULL")
    op.execute("UPDATE products SET intended_use = '' WHERE intended_use IS NULL")
    op.execute("UPDATE products SET product_type = 'software' WHERE product_type IS NULL")

    op.alter_column("products", "manufacturer_name", nullable=False)
    op.alter_column("products", "intended_use", nullable=False)
    op.alter_column("products", "product_type", nullable=False)

    op.drop_column("products", "classification")
    op.drop_column("products", "conformity_route")
    op.drop_column("products", "market_placement_blocked")
    op.drop_column("products", "support_period_months")
    op.drop_column("products", "owner_id")

    op.add_column("product_releases", sa.Column("planned_release_date", sa.DateTime(timezone=True), nullable=True))
    op.add_column("product_releases", sa.Column("actual_release_date", sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        "product_releases",
        sa.Column(
            "classification_snapshot",
            product_classification,
            nullable=False,
            server_default="normal",
        ),
    )
    op.add_column(
        "product_releases",
        sa.Column(
            "conformity_route_snapshot",
            conformity_route,
            nullable=False,
            server_default="undecided",
        ),
    )
    op.add_column("product_releases", sa.Column("release_notes", sa.Text(), nullable=True))

    op.execute("UPDATE product_releases SET actual_release_date = released_at")
    op.execute("UPDATE product_releases SET classification_snapshot = 'normal'")
    op.execute("UPDATE product_releases SET conformity_route_snapshot = 'undecided'")

    op.drop_column("product_releases", "release_gate_status")
    op.drop_column("product_releases", "known_exploitable_vulnerabilities_count")
    op.drop_column("product_releases", "required_artifacts_complete")
    op.drop_column("product_releases", "authority_package_generated_at")
    op.drop_column("product_releases", "released_at")

    op.create_table(
        "remote_processing_elements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("provider_name", sa.String(length=255), nullable=True),
        sa.Column("data_processed", sa.Text(), nullable=True),
        sa.Column("geographic_location", sa.String(length=255), nullable=True),
        sa.Column("criticality", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_remote_processing_elements_product_id", "remote_processing_elements", ["product_id"], unique=False)
    op.create_index("ix_remote_processing_elements_name", "remote_processing_elements", ["name"], unique=False)

    op.create_table(
        "product_scope_evaluations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("is_digital_product", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("has_network_connectivity", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("performs_remote_data_processing", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("safety_component", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("used_in_critical_sector", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("handles_sensitive_functions", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("excluded_category", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("in_scope", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("recommended_classification", product_classification, nullable=False),
        sa.Column("suggested_conformity_route", conformity_route, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_product_scope_evaluations_product_id", "product_scope_evaluations", ["product_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_product_scope_evaluations_product_id", table_name="product_scope_evaluations")
    op.drop_table("product_scope_evaluations")

    op.drop_index("ix_remote_processing_elements_name", table_name="remote_processing_elements")
    op.drop_index("ix_remote_processing_elements_product_id", table_name="remote_processing_elements")
    op.drop_table("remote_processing_elements")

    op.add_column("product_releases", sa.Column("released_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("product_releases", sa.Column("authority_package_generated_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("product_releases", sa.Column("required_artifacts_complete", sa.Boolean(), nullable=False, server_default=sa.text("false")))
    op.add_column("product_releases", sa.Column("known_exploitable_vulnerabilities_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("product_releases", sa.Column("release_gate_status", postgresql.ENUM("pass", "fail", "warning", name="gatestatus", create_type=False), nullable=False, server_default="warning"))

    op.drop_column("product_releases", "release_notes")
    op.drop_column("product_releases", "conformity_route_snapshot")
    op.drop_column("product_releases", "classification_snapshot")
    op.drop_column("product_releases", "actual_release_date")
    op.drop_column("product_releases", "planned_release_date")

    op.add_column("products", sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("products", sa.Column("support_period_months", sa.Integer(), nullable=True))
    op.add_column("products", sa.Column("market_placement_blocked", sa.Boolean(), nullable=False, server_default=sa.text("true")))
    op.add_column("products", sa.Column("conformity_route", postgresql.ENUM("self_assessment", "third_party_assessment", "not_applicable", "undecided", name="conformityroute", create_type=False), nullable=False, server_default="undecided"))
    op.add_column("products", sa.Column("classification", postgresql.ENUM("normal", "important_class_1", "important_class_2", "critical", name="productclassification", create_type=False), nullable=False, server_default="normal"))

    op.drop_index("ix_products_scope_status", table_name="products")
    op.drop_index("ix_products_product_type", table_name="products")
    op.drop_index("ix_products_parent_product_id", table_name="products")
    op.drop_constraint("fk_products_parent_product_id_products", "products", type_="foreignkey")

    op.drop_column("products", "scope_status")
    op.drop_column("products", "current_classification")
    op.drop_column("products", "product_type")
    op.drop_column("products", "intended_use")
    op.drop_column("products", "manufacturer_name")
    op.drop_column("products", "parent_product_id")