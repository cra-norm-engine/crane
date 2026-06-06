"""ENISA SRP: add incident_reports table and missing vulnerability report fields

Revision ID: 20260606_0047
Revises: 20260530_0046
Create Date: 2026-06-06

Adds full ENISA SRP support:
  1. New table: incident_reports — covers the 'severe incident' branch of CRA Art. 14
     with all i13–i25 SRP fields and three-phase ENISA submission tracking.
     Final report deadline for incidents is 1 month (not 14 days as for vulnerabilities).
  2. New columns on vulnerability_reports — fills the six gaps identified against the
     ENISA SRP field table: euvd_id (v14), corrective_measures_taken (v18),
     user_corrective_measures (v19), information_sensitivity (v20),
     vulnerability_impact (v24), malicious_actor_info (v25).
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260606_0047"
down_revision = "20260530_0046"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- 1. New ENUM types for incident_reports (idempotent) ---
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE incidentreportstatus AS ENUM
                ('reported', 'triaged', 'contained', 'resolved', 'closed');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE incidentseveritycriteria AS ENUM
                ('data_protection_impact', 'malicious_code_execution', 'both');
        EXCEPTION WHEN duplicate_object THEN NULL;
        END $$;
    """)

    # --- 2. New table: incident_reports ---
    op.create_table(
        "incident_reports",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("product_release_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        # i13 — suspected malicious / unlawful act (mandatory at 24h)
        sa.Column("suspected_malicious_act", sa.Boolean(), nullable=False, server_default="false"),
        # i14–i19 — required by 72h submission
        sa.Column("incident_nature", sa.Text(), nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("initial_assessment", sa.Text(), nullable=True),
        sa.Column("corrective_measures_taken", sa.Text(), nullable=True),
        sa.Column("user_corrective_measures", sa.Text(), nullable=True),
        # i20 — sensitivity flag
        sa.Column("information_sensitivity", sa.String(255), nullable=True),
        # i21–i25 — required in final report (1 month after 72h notification)
        sa.Column("severity_criteria", postgresql.ENUM(name="incidentseveritycriteria", create_type=False), nullable=True),
        sa.Column("severity", sa.String(50), nullable=True),
        sa.Column("incident_impact", sa.Text(), nullable=True),
        sa.Column("threat_type_root_cause", sa.Text(), nullable=True),
        sa.Column("applied_mitigations", sa.Text(), nullable=True),
        # Internal lifecycle
        sa.Column("status", postgresql.ENUM(name="incidentreportstatus", create_type=False), nullable=False, server_default="reported"),
        sa.Column("assigned_to_user_id", sa.UUID(), nullable=True),
        # ENISA SRP submission tracking
        sa.Column("enisa_reporting_required", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("enisa_early_warning_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("enisa_initial_report_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("enisa_final_report_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("enisa_reference_number", sa.String(255), nullable=True),
        # Constraints
        sa.ForeignKeyConstraint(["product_release_id"], ["product_releases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["assigned_to_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_incident_reports_product_release_id", "incident_reports", ["product_release_id"], if_not_exists=True)
    op.create_index("ix_incident_reports_status", "incident_reports", ["status"], if_not_exists=True)
    op.create_index("ix_incident_reports_enisa_reporting_required", "incident_reports", ["enisa_reporting_required"], if_not_exists=True)

    # --- 3. New columns on vulnerability_reports (skip if already added) ---
    bind = op.get_bind()
    existing_cols = {
        row[0] for row in bind.execute(
            sa.text("SELECT column_name FROM information_schema.columns WHERE table_name='vulnerability_reports'")
        )
    }
    if "euvd_id" not in existing_cols:
        op.add_column("vulnerability_reports", sa.Column("euvd_id", sa.String(100), nullable=True))
    if "corrective_measures_taken" not in existing_cols:
        op.add_column("vulnerability_reports", sa.Column("corrective_measures_taken", sa.Text(), nullable=True))
    if "user_corrective_measures" not in existing_cols:
        op.add_column("vulnerability_reports", sa.Column("user_corrective_measures", sa.Text(), nullable=True))
    if "information_sensitivity" not in existing_cols:
        op.add_column("vulnerability_reports", sa.Column("information_sensitivity", sa.String(255), nullable=True))
    if "vulnerability_impact" not in existing_cols:
        op.add_column("vulnerability_reports", sa.Column("vulnerability_impact", sa.Text(), nullable=True))
    if "malicious_actor_info" not in existing_cols:
        op.add_column("vulnerability_reports", sa.Column("malicious_actor_info", sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove columns added to vulnerability_reports
    op.drop_column("vulnerability_reports", "malicious_actor_info")
    op.drop_column("vulnerability_reports", "vulnerability_impact")
    op.drop_column("vulnerability_reports", "information_sensitivity")
    op.drop_column("vulnerability_reports", "user_corrective_measures")
    op.drop_column("vulnerability_reports", "corrective_measures_taken")
    op.drop_column("vulnerability_reports", "euvd_id")

    # Drop incident_reports table and its indexes
    op.drop_index("ix_incident_reports_enisa_reporting_required", table_name="incident_reports")
    op.drop_index("ix_incident_reports_status", table_name="incident_reports")
    op.drop_index("ix_incident_reports_product_release_id", table_name="incident_reports")
    op.drop_table("incident_reports")

    op.execute("DROP TYPE IF EXISTS incidentseveritycriteria")
    op.execute("DROP TYPE IF EXISTS incidentreportstatus")
