"""Trace technical requirements to CRA essentials and pin release proof.

Revision ID: 20261009_0089
Revises: 20261003_0088
"""
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "20261009_0089"
down_revision = "20261003_0088"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("requirement_sources_identifier_key", "requirement_sources", type_="unique")
    op.execute("UPDATE requirement_sources SET edition = '' WHERE edition IS NULL")
    op.alter_column("requirement_sources", "edition", nullable=False, server_default="")
    op.create_unique_constraint("uq_requirement_source_edition", "requirement_sources", ["identifier", "edition"])
    op.drop_index("ix_annex_requirements_code", table_name="annex_requirements")
    op.create_index("ix_annex_requirements_code", "annex_requirements", ["code"])
    op.create_unique_constraint("uq_requirement_source_code", "annex_requirements", ["source_id", "code"])
    op.add_column("annex_requirements", sa.Column("acceptance_criteria", sa.Text()))
    op.create_table(
        "requirement_contributions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("technical_requirement_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("annex_requirements.id", ondelete="CASCADE"), nullable=False),
        sa.Column("essential_requirement_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("annex_requirements.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("contribution", sa.Text(), nullable=False),
        sa.UniqueConstraint("technical_requirement_id", "essential_requirement_id", name="uq_requirement_contribution"),
        sa.CheckConstraint("technical_requirement_id <> essential_requirement_id", name="ck_requirement_contribution_distinct"),
    )
    for column in ("technical_requirement_id", "essential_requirement_id"):
        op.create_index(f"ix_requirement_contributions_{column}", "requirement_contributions", [column])
    op.add_column("release_requirement_baselines", sa.Column("requirement_snapshot", postgresql.JSONB()))
    # Pin the content currently available; approval snapshots remain untouched.
    op.execute("""UPDATE release_requirement_baselines b SET requirement_snapshot =
        to_jsonb(r) || jsonb_build_object(
            'source_identifier', s.identifier, 'source_title', s.title,
            'source_edition', s.edition,
            'kind', CASE WHEN s.is_system_managed THEN 'essential' ELSE 'technical' END,
            'contributions', '[]'::jsonb)
        FROM annex_requirements r JOIN requirement_sources s ON s.id = r.source_id
        WHERE b.requirement_id = r.id""")
    op.add_column("product_requirement_decisions", sa.Column("validation_notes", sa.Text()))
    op.add_column("product_requirement_decisions", sa.Column("verification_result", sa.String(20)))
    op.add_column("product_requirement_decisions", sa.Column("validated_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL")))
    op.add_column("product_requirement_decisions", sa.Column("validated_at", sa.DateTime(timezone=True)))
    # Preserve old approved assessments; open work must receive an explicit review.
    op.execute("""UPDATE product_requirement_decisions d SET
        validation_notes = 'Approved under the previous assessment workflow.', verification_result = 'pass',
        validated_by_user_id = a.approved_by_user_id, validated_at = a.approved_at
        FROM release_requirement_assessments a
        WHERE a.product_release_id = d.product_release_id AND a.status = 'approved'
        AND d.implementation_status = 'validated'""")
    op.execute("""UPDATE product_requirement_decisions SET implementation_status = 'implemented'
        WHERE implementation_status = 'validated' AND validation_notes IS NULL""")
    op.add_column("requirement_mapping_artifact_links", sa.Column("artifact_revision_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("artifact_revisions.id", ondelete="RESTRICT")))
    op.execute("""UPDATE requirement_mapping_artifact_links l SET artifact_revision_id = (
        SELECT r.id FROM artifact_revisions r WHERE r.artifact_id = l.artifact_id
        ORDER BY r.revision_number DESC LIMIT 1)""")


def downgrade() -> None:
    # Uniqueness restoration deliberately fails if newer editions reuse identifiers/codes.
    op.drop_column("requirement_mapping_artifact_links", "artifact_revision_id")
    for column in ("validated_at", "validated_by_user_id", "validation_notes", "verification_result"):
        op.drop_column("product_requirement_decisions", column)
    op.drop_column("release_requirement_baselines", "requirement_snapshot")
    op.drop_table("requirement_contributions")
    op.drop_column("annex_requirements", "acceptance_criteria")
    op.drop_constraint("uq_requirement_source_code", "annex_requirements", type_="unique")
    op.drop_index("ix_annex_requirements_code", table_name="annex_requirements")
    op.create_index("ix_annex_requirements_code", "annex_requirements", ["code"], unique=True)
    op.drop_constraint("uq_requirement_source_edition", "requirement_sources", type_="unique")
    op.create_unique_constraint("requirement_sources_identifier_key", "requirement_sources", ["identifier"])
    op.alter_column("requirement_sources", "edition", nullable=True, server_default=None)
