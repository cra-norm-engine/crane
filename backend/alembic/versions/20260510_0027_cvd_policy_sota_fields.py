"""Extend cvd_policies with state-of-the-art CVD policy fields.

Adds: pgp_key_url, security_txt_url, bug_bounty_url, response_sla_hours,
      safe_harbor, acknowledgement_offered, scope_description,
      out_of_scope_description, supported_versions.

Revision ID: 20260510_0027
Revises: 20260510_0026
Create Date: 2026-05-10
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260510_0027"
down_revision = "20260510_0026"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("cvd_policies", sa.Column("pgp_key_url", sa.String(2048), nullable=True))
    op.add_column("cvd_policies", sa.Column("security_txt_url", sa.String(2048), nullable=True))
    op.add_column("cvd_policies", sa.Column("bug_bounty_url", sa.String(2048), nullable=True))
    op.add_column("cvd_policies", sa.Column("response_sla_hours", sa.Integer(), nullable=False, server_default="48"))
    op.add_column("cvd_policies", sa.Column("safe_harbor", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("cvd_policies", sa.Column("acknowledgement_offered", sa.Boolean(), nullable=False, server_default="false"))
    op.add_column("cvd_policies", sa.Column("scope_description", sa.Text(), nullable=True))
    op.add_column("cvd_policies", sa.Column("out_of_scope_description", sa.Text(), nullable=True))
    op.add_column("cvd_policies", sa.Column("supported_versions", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("cvd_policies", "supported_versions")
    op.drop_column("cvd_policies", "out_of_scope_description")
    op.drop_column("cvd_policies", "scope_description")
    op.drop_column("cvd_policies", "acknowledgement_offered")
    op.drop_column("cvd_policies", "safe_harbor")
    op.drop_column("cvd_policies", "response_sla_hours")
    op.drop_column("cvd_policies", "bug_bounty_url")
    op.drop_column("cvd_policies", "security_txt_url")
    op.drop_column("cvd_policies", "pgp_key_url")
