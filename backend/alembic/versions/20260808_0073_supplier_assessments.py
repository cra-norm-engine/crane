"""add CRA supplier due-diligence assessments"""
from alembic import op
import sqlalchemy as sa
import uuid
from datetime import datetime, timezone

revision = "20260808_0073"
down_revision = "20260731_0072"
branch_labels = None
depends_on = None


def _timestamps() -> list[sa.Column]:
    return [
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    ]


def upgrade() -> None:
    op.create_table("suppliers", *_timestamps(),
        sa.Column("name", sa.String(255), nullable=False), sa.Column("supplier_type", sa.String(40), nullable=False),
        sa.Column("country_code", sa.String(2)), sa.Column("security_contact", sa.String(320)), sa.Column("website", sa.String(2048)),
        sa.Column("status", sa.String(30), nullable=False), sa.Column("owner_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("notes", sa.Text()), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("name", name="uq_suppliers_name"))
    op.create_index("ix_suppliers_name", "suppliers", ["name"]); op.create_index("ix_suppliers_status", "suppliers", ["status"])
    op.create_index("ix_suppliers_owner_user_id", "suppliers", ["owner_user_id"])
    op.create_table("third_party_components", *_timestamps(),
        sa.Column("supplier_id", sa.Uuid(), sa.ForeignKey("suppliers.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False), sa.Column("version", sa.String(100)), sa.Column("component_type", sa.String(30), nullable=False),
        sa.Column("purl", sa.String(1024)), sa.Column("cpe", sa.String(1024)), sa.Column("part_number", sa.String(255)),
        sa.Column("support_end_date", sa.Date()), sa.Column("update_channel", sa.String(2048)), sa.Column("notes", sa.Text()),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("supplier_id", "name", "version", name="uq_supplier_component_version"))
    op.create_index("ix_third_party_components_supplier_id", "third_party_components", ["supplier_id"])
    op.create_index("ix_third_party_components_name", "third_party_components", ["name"])
    op.create_index("ix_third_party_components_purl", "third_party_components", ["purl"])
    op.create_table("product_component_links", *_timestamps(),
        sa.Column("product_release_id", sa.Uuid(), sa.ForeignKey("product_releases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("component_id", sa.Uuid(), sa.ForeignKey("third_party_components.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sbom_record_id", sa.Uuid(), sa.ForeignKey("sbom_records.id", ondelete="SET NULL")),
        sa.Column("is_direct", sa.Boolean(), nullable=False), sa.Column("is_core_function", sa.Boolean(), nullable=False),
        sa.Column("criticality", sa.String(20), nullable=False), sa.Column("criticality_rationale", sa.Text(), nullable=False),
        sa.Column("usage_context", sa.Text()), sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_release_id", "component_id", name="uq_release_third_party_component"))
    for col in ("product_release_id", "component_id", "sbom_record_id", "criticality"): op.create_index(f"ix_product_component_links_{col}", "product_component_links", [col])
    op.create_table("supplier_assessments", *_timestamps(),
        sa.Column("supplier_id", sa.Uuid(), sa.ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("component_id", sa.Uuid(), sa.ForeignKey("third_party_components.id", ondelete="SET NULL")),
        sa.Column("product_release_id", sa.Uuid(), sa.ForeignKey("product_releases.id", ondelete="SET NULL")),
        sa.Column("system_version", sa.Integer(), nullable=False), sa.Column("title", sa.String(255), nullable=False),
        sa.Column("assessment_tier", sa.String(20), nullable=False), sa.Column("tier_rationale", sa.Text(), nullable=False),
        sa.Column("methodology", sa.Text(), nullable=False), sa.Column("status", sa.String(40), nullable=False),
        sa.Column("conclusion", sa.Text()), sa.Column("valid_until", sa.Date()),
        sa.Column("owner_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("reviewer_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("submitted_at", sa.DateTime(timezone=True)), sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("rejection_reason", sa.Text()), sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("supplier_id", "system_version", name="uq_supplier_assessment_version"))
    for col in ("supplier_id", "component_id", "product_release_id", "status", "owner_user_id", "reviewer_user_id"): op.create_index(f"ix_supplier_assessments_{col}", "supplier_assessments", [col])
    op.add_column("evidence_items", sa.Column("supplier_assessment_id", sa.Uuid(), sa.ForeignKey("supplier_assessments.id", ondelete="SET NULL")))
    op.create_index("ix_evidence_items_supplier_assessment_id", "evidence_items", ["supplier_assessment_id"])
    op.create_table("supplier_assessment_responses", *_timestamps(),
        sa.Column("assessment_id", sa.Uuid(), sa.ForeignKey("supplier_assessments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("criterion_key", sa.String(100), nullable=False), sa.Column("criterion_title", sa.String(255), nullable=False),
        sa.Column("decision", sa.String(30), nullable=False), sa.Column("rationale", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("assessment_id", "criterion_key", name="uq_assessment_criterion"))
    op.create_index("ix_supplier_assessment_responses_assessment_id", "supplier_assessment_responses", ["assessment_id"])
    op.create_table("supplier_assessment_evidence_links", *_timestamps(),
        sa.Column("assessment_id", sa.Uuid(), sa.ForeignKey("supplier_assessments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("response_id", sa.Uuid(), sa.ForeignKey("supplier_assessment_responses.id", ondelete="SET NULL")),
        sa.Column("evidence_item_id", sa.Uuid(), sa.ForeignKey("evidence_items.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("issued_at", sa.Date()), sa.Column("valid_until", sa.Date()), sa.Column("review_status", sa.String(30), nullable=False),
        sa.Column("reviewed_by_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)), sa.Column("review_notes", sa.Text()), sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("assessment_id", "evidence_item_id", name="uq_assessment_evidence"))
    for col in ("assessment_id", "response_id", "evidence_item_id"): op.create_index(f"ix_supplier_assessment_evidence_links_{col}", "supplier_assessment_evidence_links", [col])
    op.create_table("supplier_findings", *_timestamps(),
        sa.Column("assessment_id", sa.Uuid(), sa.ForeignKey("supplier_assessments.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False), sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False), sa.Column("mitigation_plan", sa.Text(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False), sa.Column("owner_user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("due_date", sa.Date()), sa.Column("risk_item_id", sa.Uuid(), sa.ForeignKey("risk_items.id", ondelete="SET NULL")),
        sa.PrimaryKeyConstraint("id"))
    for col in ("assessment_id", "severity", "status", "owner_user_id", "risk_item_id"): op.create_index(f"ix_supplier_findings_{col}", "supplier_findings", [col])

    bind = op.get_bind()
    now = datetime.now(timezone.utc)
    grants = {
        "supplier_assessment_read": {"admin", "legal_team", "product_owner", "product_management", "cybersecurity_engineer"},
        "supplier_assessment_write": {"admin", "product_owner", "cybersecurity_engineer"},
        "supplier_assessment_approve": {"admin", "legal_team", "cybersecurity_engineer"},
    }
    for key, role_names in grants.items():
        permission_id = bind.execute(sa.text("select id from permissions where key=:key"), {"key": key}).scalar()
        if permission_id is None:
            permission_id = uuid.uuid4()
            bind.execute(sa.text("insert into permissions(id,key,description,created_at,updated_at) values (:id,:key,:description,:now,:now)"),
                {"id": permission_id, "key": key, "description": key.replace("_", " ").title(), "now": now})
        for role_name in role_names:
            role_id = bind.execute(sa.text("select id from roles where name=:name"), {"name": role_name}).scalar()
            if role_id is not None:
                bind.execute(sa.text("insert into role_permissions(id,role_id,permission_id) select :id,:role_id,:permission_id where not exists (select 1 from role_permissions where role_id=:role_id and permission_id=:permission_id)"),
                    {"id": uuid.uuid4(), "role_id": role_id, "permission_id": permission_id})


def downgrade() -> None:
    bind = op.get_bind()
    bind.execute(sa.text("delete from role_permissions where permission_id in (select id from permissions where key like 'supplier_assessment_%')"))
    bind.execute(sa.text("delete from permissions where key like 'supplier_assessment_%'"))
    op.drop_index("ix_evidence_items_supplier_assessment_id", table_name="evidence_items")
    op.drop_column("evidence_items", "supplier_assessment_id")
    for table in ("supplier_findings", "supplier_assessment_evidence_links", "supplier_assessment_responses", "supplier_assessments", "product_component_links", "third_party_components", "suppliers"):
        op.drop_table(table)
