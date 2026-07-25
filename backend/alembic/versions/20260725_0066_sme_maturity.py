"""SME maturity assessments, improvement actions, and evidence links."""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260725_0066"
down_revision = "20260717_0065"
branch_labels = None
depends_on = None


def upgrade() -> None:
    uuid = postgresql.UUID(as_uuid=True)
    def timestamps():
        return [sa.Column("id", uuid, primary_key=True), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False)]

    op.create_table("maturity_model_versions", *timestamps(), sa.Column("code", sa.String(50), nullable=False, unique=True), sa.Column("title", sa.String(255), nullable=False), sa.Column("source", sa.String(255), nullable=False), sa.Column("published_on", sa.Date(), nullable=False), sa.Column("attribution", sa.Text(), nullable=False), sa.Column("catalog_json", postgresql.JSONB(), nullable=False))
    op.create_table("maturity_assessments", *timestamps(), sa.Column("model_version_id", uuid, sa.ForeignKey("maturity_model_versions.id", ondelete="RESTRICT"), nullable=False), sa.Column("title", sa.String(255), nullable=False), sa.Column("scope", sa.Text(), nullable=False), sa.Column("period_start", sa.Date()), sa.Column("period_end", sa.Date()), sa.Column("status", sa.String(20), nullable=False), sa.Column("assessor_user_id", uuid, sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False), sa.Column("reviewer_user_id", uuid, sa.ForeignKey("users.id", ondelete="SET NULL")), sa.Column("submitted_at", sa.DateTime(timezone=True)), sa.Column("approved_at", sa.DateTime(timezone=True)), sa.Column("reviewer_justification", sa.Text()), sa.Column("reassessment_due_date", sa.Date()), sa.Column("catalog_snapshot_json", postgresql.JSONB(), nullable=False))
    op.create_index("ix_maturity_assessments_status", "maturity_assessments", ["status"])
    op.create_table("maturity_responses", *timestamps(), sa.Column("assessment_id", uuid, sa.ForeignKey("maturity_assessments.id", ondelete="CASCADE"), nullable=False), sa.Column("question_code", sa.String(10), nullable=False), sa.Column("score", sa.Integer()), sa.Column("rationale", sa.Text()), sa.Column("confidence", sa.String(20)), sa.Column("assessor_notes", sa.Text()), sa.UniqueConstraint("assessment_id", "question_code", name="uq_maturity_response_question"))
    op.create_index("ix_maturity_responses_assessment_id", "maturity_responses", ["assessment_id"])
    op.create_table("maturity_evidence_links", *timestamps(), sa.Column("response_id", uuid, sa.ForeignKey("maturity_responses.id", ondelete="CASCADE"), nullable=False), sa.Column("entity_type", sa.String(50), nullable=False), sa.Column("entity_id", uuid, nullable=False), sa.Column("label", sa.String(255), nullable=False), sa.Column("added_by_user_id", uuid, sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False))
    op.create_index("ix_maturity_evidence_links_response_id", "maturity_evidence_links", ["response_id"])
    op.create_table("maturity_improvement_actions", *timestamps(), sa.Column("assessment_id", uuid, sa.ForeignKey("maturity_assessments.id", ondelete="CASCADE"), nullable=False), sa.Column("question_code", sa.String(10)), sa.Column("domain_code", sa.String(10), nullable=False), sa.Column("title", sa.String(500), nullable=False), sa.Column("priority", sa.String(20), nullable=False), sa.Column("status", sa.String(20), nullable=False), sa.Column("owner_user_id", uuid, sa.ForeignKey("users.id", ondelete="SET NULL")), sa.Column("due_date", sa.Date()), sa.Column("comments", sa.Text()), sa.Column("completion_evidence", sa.Text()))
    op.create_index("ix_maturity_improvement_actions_assessment_id", "maturity_improvement_actions", ["assessment_id"])


def downgrade() -> None:
    for table in ("maturity_improvement_actions", "maturity_evidence_links", "maturity_responses", "maturity_assessments", "maturity_model_versions"):
        op.drop_table(table)
