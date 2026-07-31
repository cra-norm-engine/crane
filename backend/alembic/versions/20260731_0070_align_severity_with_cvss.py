"""align vulnerability severity with authoritative CVSS scores"""
from __future__ import annotations

from alembic import op

revision = "20260731_0070"
down_revision = "20260731_0069"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE sbom_vulnerability_findings
        SET severity = CASE
            WHEN cvss_score >= 9.0 THEN 'CRITICAL'
            WHEN cvss_score >= 7.0 THEN 'HIGH'
            WHEN cvss_score >= 4.0 THEN 'MEDIUM'
            WHEN cvss_score > 0 THEN 'LOW'
            ELSE 'INFORMATIONAL'
        END
        WHERE cvss_score IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE vulnerability_reports AS report
        SET cvss_score = COALESCE(report.cvss_score, finding.cvss_score),
            severity = CASE
                WHEN COALESCE(report.cvss_score, finding.cvss_score) >= 9.0 THEN 'critical'
                WHEN COALESCE(report.cvss_score, finding.cvss_score) >= 7.0 THEN 'high'
                WHEN COALESCE(report.cvss_score, finding.cvss_score) >= 4.0 THEN 'medium'
                WHEN COALESCE(report.cvss_score, finding.cvss_score) > 0 THEN 'low'
                ELSE 'informational'
            END,
            priority_policy_id = NULL
        FROM sbom_vulnerability_findings AS finding
        WHERE report.sbom_finding_id = finding.id
          AND COALESCE(report.cvss_score, finding.cvss_score) IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE vulnerability_reports
        SET severity = CASE
                WHEN cvss_score >= 9.0 THEN 'critical'
                WHEN cvss_score >= 7.0 THEN 'high'
                WHEN cvss_score >= 4.0 THEN 'medium'
                WHEN cvss_score > 0 THEN 'low'
                ELSE 'informational'
            END,
            priority_policy_id = NULL
        WHERE sbom_finding_id IS NULL AND cvss_score IS NOT NULL
        """
    )


def downgrade() -> None:
    # Previous source labels cannot be reconstructed after normalization.
    pass
