"""add policy metadata and immutable priority evaluation history"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260731_0071"
down_revision = "20260731_0070"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("vulnerability_priority_policies", sa.Column("change_reason", sa.Text(), nullable=True))
    op.execute(
        "UPDATE vulnerability_priority_policies "
        "SET change_reason = 'Historical policy imported during priority history migration.' "
        "WHERE change_reason IS NULL"
    )
    op.create_table(
        "vulnerability_priority_evaluations",
        sa.Column("vulnerability_report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("policy_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("policy_version", sa.Integer(), nullable=False),
        sa.Column("priority", postgresql.ENUM(name="vulnerabilitypriority", create_type=False), nullable=False),
        sa.Column("rule_id", sa.String(100), nullable=True),
        sa.Column("rule_name", sa.String(255), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("inputs_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("trigger", sa.String(50), nullable=False),
        sa.Column("actor_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["policy_id"], ["vulnerability_priority_policies.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["vulnerability_report_id"], ["vulnerability_reports.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_vulnerability_priority_evaluations_report", "vulnerability_priority_evaluations", ["vulnerability_report_id"])
    op.create_index("ix_vulnerability_priority_evaluations_policy", "vulnerability_priority_evaluations", ["policy_id"])
    op.create_index("ix_vulnerability_priority_evaluations_version", "vulnerability_priority_evaluations", ["policy_version"])
    op.execute(
        """
        INSERT INTO vulnerability_priority_evaluations (
            id, vulnerability_report_id, policy_id, policy_version, priority,
            rule_id, rule_name, reason, inputs_json, trigger, actor_user_id,
            evaluated_at, created_at, updated_at
        )
        SELECT gen_random_uuid(), report.id, report.priority_policy_id,
               COALESCE(report.priority_policy_version, 0), report.priority,
               report.priority_rule_id, report.priority_rule_name,
               COALESCE(report.priority_reason, 'Historical decision imported.'),
               jsonb_build_object(
                   'severity', report.severity,
                   'cvss_score', COALESCE(report.cvss_score, finding.cvss_score),
                   'epss_score', finding.epss_score,
                   'is_known_exploited', COALESCE(finding.is_known_exploited, false),
                   'exposure', report.exposure,
                   'asset_criticality', report.asset_criticality,
                   'impact_level', report.impact_level,
                   'is_exploitable', report.is_exploitable,
                   'source', report.source,
                   'status', report.status
               ),
               'history_backfill', NULL,
               COALESCE(report.priority_evaluated_at, report.updated_at),
               COALESCE(report.priority_evaluated_at, report.updated_at),
               COALESCE(report.priority_evaluated_at, report.updated_at)
        FROM vulnerability_reports AS report
        LEFT JOIN sbom_vulnerability_findings AS finding ON finding.id = report.sbom_finding_id
        """
    )


def downgrade() -> None:
    op.drop_index("ix_vulnerability_priority_evaluations_version", table_name="vulnerability_priority_evaluations")
    op.drop_index("ix_vulnerability_priority_evaluations_policy", table_name="vulnerability_priority_evaluations")
    op.drop_index("ix_vulnerability_priority_evaluations_report", table_name="vulnerability_priority_evaluations")
    op.drop_table("vulnerability_priority_evaluations")
    op.drop_column("vulnerability_priority_policies", "change_reason")
