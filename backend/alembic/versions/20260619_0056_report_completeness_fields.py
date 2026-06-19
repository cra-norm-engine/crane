"""Add fields that close the compliance-report 'Not recorded in CRANE' gaps.

Economic operators, Annex III/IV category and Annex II checklist on the product;
conformity module / notified-body number / standards, fuller DoC + CE marking and
multi-role sign-off on the release; CSIRT coordinator on the CVD policy.

Revision ID: 20260619_0056
Revises: 20260618_0055
Create Date: 2026-06-19
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

revision = "20260619_0056"
down_revision = "20260618_0055"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("products", sa.Column("authorised_representative", sa.Text(), nullable=True))
    op.add_column("products", sa.Column("importers", sa.Text(), nullable=True))
    op.add_column("products", sa.Column("distributors", sa.Text(), nullable=True))
    op.add_column("products", sa.Column("single_point_of_contact", sa.Text(), nullable=True))
    op.add_column("products", sa.Column("annex_category", sa.Text(), nullable=True))
    op.add_column("products", sa.Column("annex_ii_json", JSONB(), nullable=True))

    op.add_column("product_releases", sa.Column("eu_doc_signatory", sa.String(length=255), nullable=True))
    op.add_column("product_releases", sa.Column("eu_doc_url", sa.String(length=2048), nullable=True))
    op.add_column("product_releases", sa.Column("eu_doc_status", sa.String(length=50), nullable=True))
    op.add_column("product_releases", sa.Column("ce_marking_info", sa.Text(), nullable=True))
    op.add_column("product_releases", sa.Column("conformity_module", sa.String(length=255), nullable=True))
    op.add_column("product_releases", sa.Column("notified_body_number", sa.String(length=255), nullable=True))
    op.add_column("product_releases", sa.Column("standards_applied", sa.Text(), nullable=True))
    op.add_column("product_releases", sa.Column("signoff_compliance_lead", sa.String(length=255), nullable=True))
    op.add_column("product_releases", sa.Column("signoff_notified_body_reviewer", sa.String(length=255), nullable=True))
    op.add_column("product_releases", sa.Column("signoff_executive", sa.String(length=255), nullable=True))

    op.add_column("cvd_policies", sa.Column("coordinator_csirt", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("cvd_policies", "coordinator_csirt")
    for col in ("signoff_executive", "signoff_notified_body_reviewer", "signoff_compliance_lead",
                "standards_applied", "notified_body_number", "conformity_module",
                "ce_marking_info", "eu_doc_status", "eu_doc_url", "eu_doc_signatory"):
        op.drop_column("product_releases", col)
    for col in ("annex_ii_json", "annex_category", "single_point_of_contact",
                "distributors", "importers", "authorised_representative"):
        op.drop_column("products", col)
