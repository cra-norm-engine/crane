"""add governed requirement sources and release baselines

Revision ID: 20261003_0088
Revises: 20261002_0087
"""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision = "20261003_0088"
down_revision = "20261002_0087"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "requirement_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("identifier", sa.String(100), nullable=False, unique=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("source_type", sa.String(50), nullable=False),
        sa.Column("edition", sa.String(100)),
        sa.Column("publisher", sa.String(255)),
        sa.Column("reference_url", sa.String(2048)),
        sa.Column("license_note", sa.Text()),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("organization_wide", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_system_managed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.create_index("ix_requirement_sources_identifier", "requirement_sources", ["identifier"])
    op.create_index("ix_requirement_sources_source_type", "requirement_sources", ["source_type"])
    op.create_index("ix_requirement_sources_status", "requirement_sources", ["status"])
    op.create_table(
        "requirement_source_products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["requirement_sources.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("source_id", "product_id", name="uq_requirement_source_product"),
    )
    op.create_index("ix_requirement_source_products_source_id", "requirement_source_products", ["source_id"])
    op.create_index("ix_requirement_source_products_product_id", "requirement_source_products", ["product_id"])
    columns = (
        sa.Column("source_id", postgresql.UUID(as_uuid=True)),
        sa.Column("clause_reference", sa.String(100)),
        sa.Column("applicability_guidance", sa.Text()),
        sa.Column("verification_guidance", sa.Text()),
        sa.Column("expected_evidence", sa.Text()),
        sa.Column("revision", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(20), nullable=False, server_default="published"),
        sa.Column("is_mandatory", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    for column in columns:
        op.add_column("annex_requirements", column)
    op.create_foreign_key("annex_requirements_source_id_fkey", "annex_requirements", "requirement_sources", ["source_id"], ["id"], ondelete="RESTRICT")
    op.create_index("ix_annex_requirements_source_id", "annex_requirements", ["source_id"])
    op.create_index("ix_annex_requirements_status", "annex_requirements", ["status"])
    op.execute("INSERT INTO requirement_sources (id, created_at, updated_at, identifier, title, source_type, status, organization_wide, is_system_managed) VALUES (gen_random_uuid(), now(), now(), 'CRA-ANNEX-I', 'CRA Annex I essential requirements', 'regulation', 'published', true, true)")
    op.execute("UPDATE annex_requirements SET source_id = (SELECT id FROM requirement_sources WHERE identifier = 'CRA-ANNEX-I'), clause_reference = code, is_mandatory = (annex_part = 'part_ii' OR code = 'ANNEX-I-PART-I-1')")
    op.alter_column("annex_requirements", "source_id", nullable=False)
    op.create_table(
        "release_requirement_baselines",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("product_release_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requirement_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("requirement_revision", sa.Integer(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(["product_release_id"], ["product_releases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requirement_id"], ["annex_requirements.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("product_release_id", "requirement_id", name="uq_release_requirement_baseline"),
    )
    op.create_index("ix_release_requirement_baselines_product_release_id", "release_requirement_baselines", ["product_release_id"])
    op.create_index("ix_release_requirement_baselines_requirement_id", "release_requirement_baselines", ["requirement_id"])
    op.execute("""INSERT INTO release_requirement_baselines (id, created_at, updated_at, product_release_id, requirement_id, requirement_revision)
        SELECT gen_random_uuid(), now(), now(), release.id, requirement.id, requirement.revision
        FROM product_releases release CROSS JOIN annex_requirements requirement
        JOIN requirement_sources source ON source.id = requirement.source_id WHERE source.is_system_managed = true""")


def downgrade() -> None:
    op.drop_table("release_requirement_baselines")
    op.drop_index("ix_annex_requirements_status", table_name="annex_requirements")
    op.drop_index("ix_annex_requirements_source_id", table_name="annex_requirements")
    op.drop_constraint("annex_requirements_source_id_fkey", "annex_requirements", type_="foreignkey")
    for column in ("is_mandatory", "status", "revision", "expected_evidence", "verification_guidance", "applicability_guidance", "clause_reference", "source_id"):
        op.drop_column("annex_requirements", column)
    op.drop_table("requirement_source_products")
    op.drop_table("requirement_sources")
