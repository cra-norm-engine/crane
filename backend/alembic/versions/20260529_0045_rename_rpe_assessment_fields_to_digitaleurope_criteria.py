"""Rename RPE assessment boolean columns to DIGITALEUROPE I1/I3/I5/I6 criteria names.

Replaces the old browser-centric decision tree fields with the four DIGITALEUROPE
inclusion criteria from the July 2025 guidance on CRA Art. 3(2) RDPS classification.
Also adds provider_is_nis2_msp to support guidance text after classification.

Old → New:
  has_downloadable_component    → is_developed_by_manufacturer   (I1)
  is_browser_only_access        → has_bidirectional_exchange      (I6)
  is_essential_to_core_function → is_necessary_for_product_function (I3)
  is_manufacturer_owned         → directly_interacts_with_product (I5)

Revision ID: 20260529_0045
Revises: 20260529_0044
Create Date: 2026-05-29
"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260529_0045"
down_revision = "20260529_0044"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename the four decision-tree boolean columns to match DIGITALEUROPE I1/I3/I5/I6 criteria.
    op.execute(
        "ALTER TABLE remote_processing_elements "
        "RENAME COLUMN has_downloadable_component TO is_developed_by_manufacturer"
    )
    op.execute(
        "ALTER TABLE remote_processing_elements "
        "RENAME COLUMN is_browser_only_access TO has_bidirectional_exchange"
    )
    op.execute(
        "ALTER TABLE remote_processing_elements "
        "RENAME COLUMN is_essential_to_core_function TO is_necessary_for_product_function"
    )
    op.execute(
        "ALTER TABLE remote_processing_elements "
        "RENAME COLUMN is_manufacturer_owned TO directly_interacts_with_product"
    )
    # Add context field for guidance text: is the provider already covered by NIS2 MSP rules?
    op.add_column(
        "remote_processing_elements",
        sa.Column("provider_is_nis2_msp", sa.Boolean(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("remote_processing_elements", "provider_is_nis2_msp")
    op.execute(
        "ALTER TABLE remote_processing_elements "
        "RENAME COLUMN directly_interacts_with_product TO is_manufacturer_owned"
    )
    op.execute(
        "ALTER TABLE remote_processing_elements "
        "RENAME COLUMN is_necessary_for_product_function TO is_essential_to_core_function"
    )
    op.execute(
        "ALTER TABLE remote_processing_elements "
        "RENAME COLUMN has_bidirectional_exchange TO is_browser_only_access"
    )
    op.execute(
        "ALTER TABLE remote_processing_elements "
        "RENAME COLUMN is_developed_by_manufacturer TO has_downloadable_component"
    )
