"""initial scaffold

Revision ID: 20260330_0001
Revises: None
Create Date: 2026-03-30 00:00:00
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260330_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    release_status = postgresql.ENUM(
        "draft",
        "in_review",
        "blocked",
        "approved",
        "released",
        "withdrawn",
        "recalled",
        "end_of_support",
        name="releasestatus",
        create_type=False,
    )
    gate_status = postgresql.ENUM(
        "pass",
        "fail",
        "warning",
        name="gatestatus",
        create_type=False,
    )
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
    evidence_type = postgresql.ENUM(
        "document",
        "test_report",
        "sbom",
        "screenshot",
        "link",
        "declaration",
        "annex_output",
        "authority_package",
        name="evidencetype",
        create_type=False,
    )

    bind = op.get_bind()
    release_status.create(bind, checkfirst=True)
    gate_status.create(bind, checkfirst=True)
    product_classification.create(bind, checkfirst=True)
    conformity_route.create(bind, checkfirst=True)
    evidence_type.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("roles", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=False)

    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("product_code", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("classification", product_classification, nullable=False),
        sa.Column("conformity_route", conformity_route, nullable=False),
        sa.Column("market_placement_blocked", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("support_period_months", sa.Integer(), nullable=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("product_code", name="uq_products_product_code"),
    )
    op.create_index("ix_products_name", "products", ["name"], unique=False)
    op.create_index("ix_products_product_code", "products", ["product_code"], unique=False)

    op.create_table(
        "product_releases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("version", sa.String(length=100), nullable=False),
        sa.Column("release_status", release_status, nullable=False),
        sa.Column("release_gate_status", gate_status, nullable=False, server_default="warning"),
        sa.Column("known_exploitable_vulnerabilities_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("required_artifacts_complete", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("authority_package_generated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("product_id", "version", name="uq_product_releases_product_version"),
    )

    op.create_table(
        "audit_log_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("actor_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("entity_name", sa.String(length=120), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("correlation_id", sa.String(length=64), nullable=True),
        sa.Column("ip_address", sa.String(length=64), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_log_events_created_at", "audit_log_events", ["created_at"], unique=False)
    op.create_index("ix_audit_log_events_entity_name", "audit_log_events", ["entity_name"], unique=False)

    op.create_table(
        "domain_placeholders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("entity_name", sa.String(length=120), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("evidence_type", evidence_type, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("domain_placeholders")
    op.drop_index("ix_audit_log_events_entity_name", table_name="audit_log_events")
    op.drop_index("ix_audit_log_events_created_at", table_name="audit_log_events")
    op.drop_table("audit_log_events")
    op.drop_table("product_releases")
    op.drop_index("ix_products_product_code", table_name="products")
    op.drop_index("ix_products_name", table_name="products")
    op.drop_table("products")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    bind = op.get_bind()
    postgresql.ENUM(name="evidencetype").drop(bind, checkfirst=True)
    postgresql.ENUM(name="conformityroute").drop(bind, checkfirst=True)
    postgresql.ENUM(name="productclassification").drop(bind, checkfirst=True)
    postgresql.ENUM(name="gatestatus").drop(bind, checkfirst=True)
    postgresql.ENUM(name="releasestatus").drop(bind, checkfirst=True)