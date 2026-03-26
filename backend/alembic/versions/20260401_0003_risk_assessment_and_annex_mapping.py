"""risk assessment and annex mapping domain

Revision ID: 20260401_0003
Revises: 20260331_0002
Create Date: 2026-04-01 00:00:00
"""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260401_0003"
down_revision = "20260331_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    risk_assessment_status = postgresql.ENUM(
        "draft",
        "in_review",
        "approved",
        "archived",
        name="riskassessmentstatus",
        create_type=False,
    )
    risk_item_status = postgresql.ENUM(
        "open",
        "in_progress",
        "mitigated",
        "accepted",
        "closed",
        name="riskitemstatus",
        create_type=False,
    )
    requirement_implementation_status = postgresql.ENUM(
        "planned",
        "in_progress",
        "implemented",
        "verified",
        "not_applicable",
        name="requirementimplementationstatus",
        create_type=False,
    )
    annex_part = postgresql.ENUM(
        "part_i",
        "part_ii",
        name="annexpart",
        create_type=False,
    )
    risk_level = postgresql.ENUM(
        "low",
        "medium",
        "high",
        "critical",
        name="risklevel",
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
    sdl_activity = postgresql.ENUM(
        "requirements",
        "design",
        "implementation",
        "verification",
        "validation",
        "vulnerability_management",
        "documentation",
        "post_market",
        name="sdlactivity",
        create_type=False,
    )

    risk_assessment_status.create(op.get_bind(), checkfirst=True)
    risk_item_status.create(op.get_bind(), checkfirst=True)
    requirement_implementation_status.create(op.get_bind(), checkfirst=True)
    annex_part.create(op.get_bind(), checkfirst=True)
    risk_level.create(op.get_bind(), checkfirst=True)
    evidence_type.create(op.get_bind(), checkfirst=True)
    sdl_activity.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "risk_assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_release_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("product_releases.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("version_label", sa.String(length=100), nullable=False),
        sa.Column("status", risk_assessment_status, nullable=False, server_default="draft"),
        sa.Column("methodology", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("product_id", "version_label", name="uq_risk_assessments_product_version_label"),
    )
    op.create_index("ix_risk_assessments_product_id", "risk_assessments", ["product_id"], unique=False)
    op.create_index("ix_risk_assessments_product_release_id", "risk_assessments", ["product_release_id"], unique=False)
    op.create_index("ix_risk_assessments_owner_user_id", "risk_assessments", ["owner_user_id"], unique=False)
    op.create_index("ix_risk_assessments_version_label", "risk_assessments", ["version_label"], unique=False)
    op.create_index("ix_risk_assessments_status", "risk_assessments", ["status"], unique=False)

    op.create_table(
        "risk_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("risk_assessment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("risk_assessments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("threat_scenario", sa.Text(), nullable=False),
        sa.Column("asset_affected", sa.String(length=255), nullable=False),
        sa.Column("likelihood", risk_level, nullable=False),
        sa.Column("impact", risk_level, nullable=False),
        sa.Column("risk_level", risk_level, nullable=False),
        sa.Column("mitigation_plan", sa.Text(), nullable=False),
        sa.Column("residual_risk_level", risk_level, nullable=True),
        sa.Column("status", risk_item_status, nullable=False, server_default="open"),
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_risk_items_risk_assessment_id", "risk_items", ["risk_assessment_id"], unique=False)
    op.create_index("ix_risk_items_title", "risk_items", ["title"], unique=False)
    op.create_index("ix_risk_items_risk_level", "risk_items", ["risk_level"], unique=False)
    op.create_index("ix_risk_items_status", "risk_items", ["status"], unique=False)
    op.create_index("ix_risk_items_owner_user_id", "risk_items", ["owner_user_id"], unique=False)

    op.create_table(
        "annex_requirements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("annex_part", annex_part, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_annex_requirements_code", "annex_requirements", ["code"], unique=True)
    op.create_index("ix_annex_requirements_title", "annex_requirements", ["title"], unique=False)
    op.create_index("ix_annex_requirements_annex_part", "annex_requirements", ["annex_part"], unique=False)
    op.create_index("ix_annex_requirements_is_active", "annex_requirements", ["is_active"], unique=False)

    op.create_table(
        "requirement_mappings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("risk_item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("risk_items.id", ondelete="SET NULL"), nullable=True),
        sa.Column("annex_requirement_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("annex_requirements.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("engineering_requirement_ref", sa.String(length=255), nullable=True),
        sa.Column("sdl_activity", sdl_activity, nullable=False),
        sa.Column("implementation_status", requirement_implementation_status, nullable=False, server_default="planned"),
        sa.Column("evidence_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_requirement_mappings_risk_item_id", "requirement_mappings", ["risk_item_id"], unique=False)
    op.create_index("ix_requirement_mappings_annex_requirement_id", "requirement_mappings", ["annex_requirement_id"], unique=False)
    op.create_index("ix_requirement_mappings_engineering_requirement_ref", "requirement_mappings", ["engineering_requirement_ref"], unique=False)
    op.create_index("ix_requirement_mappings_sdl_activity", "requirement_mappings", ["sdl_activity"], unique=False)
    op.create_index("ix_requirement_mappings_implementation_status", "requirement_mappings", ["implementation_status"], unique=False)

    op.create_table(
        "evidence_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("product_release_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("product_releases.id", ondelete="SET NULL"), nullable=True),
        sa.Column("risk_assessment_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("risk_assessments.id", ondelete="SET NULL"), nullable=True),
        sa.Column("requirement_mapping_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("requirement_mappings.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("evidence_type", evidence_type, nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=True),
        sa.Column("external_url", sa.String(length=2048), nullable=True),
        sa.Column("uploaded_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_evidence_items_product_release_id", "evidence_items", ["product_release_id"], unique=False)
    op.create_index("ix_evidence_items_risk_assessment_id", "evidence_items", ["risk_assessment_id"], unique=False)
    op.create_index("ix_evidence_items_requirement_mapping_id", "evidence_items", ["requirement_mapping_id"], unique=False)
    op.create_index("ix_evidence_items_title", "evidence_items", ["title"], unique=False)
    op.create_index("ix_evidence_items_evidence_type", "evidence_items", ["evidence_type"], unique=False)
    op.create_index("ix_evidence_items_file_path", "evidence_items", ["file_path"], unique=False)
    op.create_index("ix_evidence_items_external_url", "evidence_items", ["external_url"], unique=False)
    op.create_index("ix_evidence_items_uploaded_by_user_id", "evidence_items", ["uploaded_by_user_id"], unique=False)

    now_value = datetime.now(UTC)

    annex_requirements_table = sa.table(
        "annex_requirements",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("code", sa.String()),
        sa.column("title", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("annex_part", annex_part),
        sa.column("is_active", sa.Boolean()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )

    op.bulk_insert(
        annex_requirements_table,
        [
            {
                "id": uuid.uuid4(),
                "code": "ANNEX-I-PART-I-1",
                "title": "Security by design and by default",
                "description": "Products shall be designed, developed and produced to ensure an appropriate level of cybersecurity based on the risks.",
                "annex_part": "part_i",
                "is_active": True,
                "created_at": now_value,
                "updated_at": now_value,
            },
            {
                "id": uuid.uuid4(),
                "code": "ANNEX-I-PART-I-2",
                "title": "Address known exploitable vulnerabilities",
                "description": "Products shall be designed, developed and produced to reduce vulnerabilities and address known exploitable weaknesses where applicable.",
                "annex_part": "part_i",
                "is_active": True,
                "created_at": now_value,
                "updated_at": now_value,
            },
            {
                "id": uuid.uuid4(),
                "code": "ANNEX-I-PART-I-3",
                "title": "Secure by default configuration",
                "description": "Products shall be made available on the market with a secure by default configuration, unless otherwise agreed between manufacturer and business user in relation to a tailored product.",
                "annex_part": "part_i",
                "is_active": True,
                "created_at": now_value,
                "updated_at": now_value,
            },
            {
                "id": uuid.uuid4(),
                "code": "ANNEX-I-PART-II-1",
                "title": "Vulnerability handling and remediation",
                "description": "Manufacturers shall identify and document vulnerabilities and components, including by maintaining relevant records and enabling remediation during the support period.",
                "annex_part": "part_ii",
                "is_active": True,
                "created_at": now_value,
                "updated_at": now_value,
            },
            {
                "id": uuid.uuid4(),
                "code": "ANNEX-I-PART-II-2",
                "title": "Security updates and support period maintenance",
                "description": "Manufacturers shall address and remediate vulnerabilities without delay and maintain cybersecurity support and evidence throughout the support period.",
                "annex_part": "part_ii",
                "is_active": True,
                "created_at": now_value,
                "updated_at": now_value,
            },
        ],
    )

    roles_table = sa.table(
        "roles",
        sa.column("id", postgresql.UUID(as_uuid=True)),
        sa.column("name", sa.String()),
        sa.column("description", sa.String()),
        sa.column("created_at", sa.DateTime(timezone=True)),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )

    conn = op.get_bind()
    existing_roles = {row[0] for row in conn.execute(sa.text("SELECT name FROM roles"))}
    role_rows: list[dict[str, object]] = []

    if "cybersecurity_engineer" not in existing_roles:
        role_rows.append(
            {
                "id": uuid.uuid4(),
                "name": "cybersecurity_engineer",
                "description": "Full create and edit access for risk assessments, risk items, mappings, and evidence.",
                "created_at": now_value,
                "updated_at": now_value,
            }
        )

    if "legal_team" not in existing_roles:
        role_rows.append(
            {
                "id": uuid.uuid4(),
                "name": "legal_team",
                "description": "Read-only access to CRA compliance records and Annex mappings.",
                "created_at": now_value,
                "updated_at": now_value,
            }
        )

    if role_rows:
        op.bulk_insert(roles_table, role_rows)


def downgrade() -> None:
    conn = op.get_bind()

    conn.execute(sa.text("DELETE FROM roles WHERE name IN ('cybersecurity_engineer', 'legal_team')"))
    conn.execute(
        sa.text(
            """
            DELETE FROM annex_requirements
            WHERE code IN (
                'ANNEX-I-PART-I-1',
                'ANNEX-I-PART-I-2',
                'ANNEX-I-PART-I-3',
                'ANNEX-I-PART-II-1',
                'ANNEX-I-PART-II-2'
            )
            """
        )
    )

    op.drop_index("ix_evidence_items_uploaded_by_user_id", table_name="evidence_items")
    op.drop_index("ix_evidence_items_external_url", table_name="evidence_items")
    op.drop_index("ix_evidence_items_file_path", table_name="evidence_items")
    op.drop_index("ix_evidence_items_evidence_type", table_name="evidence_items")
    op.drop_index("ix_evidence_items_title", table_name="evidence_items")
    op.drop_index("ix_evidence_items_requirement_mapping_id", table_name="evidence_items")
    op.drop_index("ix_evidence_items_risk_assessment_id", table_name="evidence_items")
    op.drop_index("ix_evidence_items_product_release_id", table_name="evidence_items")
    op.drop_table("evidence_items")

    op.drop_index("ix_requirement_mappings_implementation_status", table_name="requirement_mappings")
    op.drop_index("ix_requirement_mappings_sdl_activity", table_name="requirement_mappings")
    op.drop_index("ix_requirement_mappings_engineering_requirement_ref", table_name="requirement_mappings")
    op.drop_index("ix_requirement_mappings_annex_requirement_id", table_name="requirement_mappings")
    op.drop_index("ix_requirement_mappings_risk_item_id", table_name="requirement_mappings")
    op.drop_table("requirement_mappings")

    op.drop_index("ix_annex_requirements_is_active", table_name="annex_requirements")
    op.drop_index("ix_annex_requirements_annex_part", table_name="annex_requirements")
    op.drop_index("ix_annex_requirements_title", table_name="annex_requirements")
    op.drop_index("ix_annex_requirements_code", table_name="annex_requirements")
    op.drop_table("annex_requirements")

    op.drop_index("ix_risk_items_owner_user_id", table_name="risk_items")
    op.drop_index("ix_risk_items_status", table_name="risk_items")
    op.drop_index("ix_risk_items_risk_level", table_name="risk_items")
    op.drop_index("ix_risk_items_title", table_name="risk_items")
    op.drop_index("ix_risk_items_risk_assessment_id", table_name="risk_items")
    op.drop_table("risk_items")

    op.drop_index("ix_risk_assessments_status", table_name="risk_assessments")
    op.drop_index("ix_risk_assessments_version_label", table_name="risk_assessments")
    op.drop_index("ix_risk_assessments_owner_user_id", table_name="risk_assessments")
    op.drop_index("ix_risk_assessments_product_release_id", table_name="risk_assessments")
    op.drop_index("ix_risk_assessments_product_id", table_name="risk_assessments")
    op.drop_table("risk_assessments")

    sdl_activity = postgresql.ENUM(
        "requirements",
        "design",
        "implementation",
        "verification",
        "validation",
        "vulnerability_management",
        "documentation",
        "post_market",
        name="sdlactivity",
    )
    requirement_implementation_status = postgresql.ENUM(
        "planned",
        "in_progress",
        "implemented",
        "verified",
        "not_applicable",
        name="requirementimplementationstatus",
    )
    risk_item_status = postgresql.ENUM(
        "open",
        "in_progress",
        "mitigated",
        "accepted",
        "closed",
        name="riskitemstatus",
    )
    risk_assessment_status = postgresql.ENUM(
        "draft",
        "in_review",
        "approved",
        "archived",
        name="riskassessmentstatus",
    )
    annex_part = postgresql.ENUM(
        "part_i",
        "part_ii",
        name="annexpart",
    )
    risk_level = postgresql.ENUM(
        "low",
        "medium",
        "high",
        "critical",
        name="risklevel",
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
    )

    evidence_type.drop(op.get_bind(), checkfirst=True)
    risk_level.drop(op.get_bind(), checkfirst=True)
    sdl_activity.drop(op.get_bind(), checkfirst=True)
    requirement_implementation_status.drop(op.get_bind(), checkfirst=True)
    risk_item_status.drop(op.get_bind(), checkfirst=True)
    risk_assessment_status.drop(op.get_bind(), checkfirst=True)
    annex_part.drop(op.get_bind(), checkfirst=True)