"""Replace severity_criteria enum with free-text incident_impact_category

Revision ID: 20260606_0048
Revises: 20260606_0047
Create Date: 2026-06-06

The severity_criteria ENUM (data_protection_impact / malicious_code_execution / both)
was not grounded in the CRA or ENISA SRP specification.  CRA Art. 14(3) just requires
a "severe incident" without enumerating sub-criteria.  The ENISA SRP form asks for a
free-text description of the incident nature and impact.

This migration:
  1. Renames the column severity_criteria → incident_impact_category
  2. Casts its type from the incidentseveritycriteria ENUM to plain TEXT
     (any existing ENUM values are preserved as their string representation)
"""
import sqlalchemy as sa
from alembic import op

revision = "20260606_0048"
down_revision = "20260606_0047"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Cast ENUM → TEXT first, then rename
    op.execute(
        "ALTER TABLE incident_reports "
        "ALTER COLUMN severity_criteria TYPE TEXT "
        "USING severity_criteria::text"
    )
    op.execute(
        "ALTER TABLE incident_reports "
        "RENAME COLUMN severity_criteria TO incident_impact_category"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE incident_reports "
        "RENAME COLUMN incident_impact_category TO severity_criteria"
    )
    # Cast back — will fail if free-text values were stored that aren't valid enum members
    op.execute(
        "ALTER TABLE incident_reports "
        "ALTER COLUMN severity_criteria TYPE incidentseveritycriteria "
        "USING severity_criteria::incidentseveritycriteria"
    )
