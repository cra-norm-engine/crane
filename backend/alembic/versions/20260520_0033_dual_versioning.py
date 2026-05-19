"""Add dual versioning (system_version + user_version) for releases and risk assessments.

System version: auto-incremented integer (v1, v2, v3, etc.)
User version: optional custom name ("Spring 2026", "RC-1", etc.)

Revision ID: 20260520_0033
Revises: 20260517_0032
Create Date: 2026-05-20
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260520_0033"
down_revision = "20260517_0032"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ========== product_releases ==========
    # Drop old unique constraint BEFORE renaming the column
    op.drop_constraint(
        "uq_product_releases_product_version",
        "product_releases",
        type_="unique",
    )

    # Add new columns
    op.add_column(
        "product_releases",
        sa.Column("system_version", sa.Integer(), nullable=True),
    )
    op.add_column(
        "product_releases",
        sa.Column("user_version", sa.String(100), nullable=True),
    )

    # Populate system_version: rank by product_id and created_at
    op.execute("""
        UPDATE product_releases
        SET system_version = ranked.version_num
        FROM (
            SELECT id, ROW_NUMBER() OVER (PARTITION BY product_id ORDER BY created_at ASC) as version_num
            FROM product_releases
        ) ranked
        WHERE product_releases.id = ranked.id
    """)

    # Make system_version NOT NULL after population
    op.alter_column("product_releases", "system_version", nullable=False)

    # Rename version column to user_version_old temporarily
    op.alter_column(
        "product_releases",
        "version",
        new_column_name="user_version_old",
    )

    # Copy old version values to user_version (keep as-is for backward compatibility)
    op.execute("""
        UPDATE product_releases
        SET user_version = user_version_old
    """)

    # Drop the old column
    op.drop_column("product_releases", "user_version_old")

    # Add new unique constraint on system_version
    op.create_unique_constraint(
        "uq_product_releases_product_system_version",
        "product_releases",
        ["product_id", "system_version"],
    )

    # Add index on system_version
    op.create_index(
        "ix_product_releases_system_version",
        "product_releases",
        ["system_version"],
    )

    # ========== risk_assessments ==========
    # Drop old unique constraint BEFORE renaming the column
    op.drop_constraint(
        "uq_risk_assessments_product_version_label",
        "risk_assessments",
        type_="unique",
    )

    # Add new columns
    op.add_column(
        "risk_assessments",
        sa.Column("system_version", sa.Integer(), nullable=True),
    )
    op.add_column(
        "risk_assessments",
        sa.Column("user_version", sa.String(100), nullable=True),
    )

    # Populate system_version: rank by product_id and created_at
    op.execute("""
        UPDATE risk_assessments
        SET system_version = ranked.version_num
        FROM (
            SELECT id, ROW_NUMBER() OVER (PARTITION BY product_id ORDER BY created_at ASC) as version_num
            FROM risk_assessments
        ) ranked
        WHERE risk_assessments.id = ranked.id
    """)

    # Make system_version NOT NULL after population
    op.alter_column("risk_assessments", "system_version", nullable=False)

    # Rename version_label column to user_version_old temporarily
    op.alter_column(
        "risk_assessments",
        "version_label",
        new_column_name="user_version_old",
    )

    # Copy old version_label values to user_version (keep as-is for backward compatibility)
    op.execute("""
        UPDATE risk_assessments
        SET user_version = user_version_old
    """)

    # Drop the old column
    op.drop_column("risk_assessments", "user_version_old")

    # Add new unique constraint on system_version
    op.create_unique_constraint(
        "uq_risk_assessments_product_system_version",
        "risk_assessments",
        ["product_id", "system_version"],
    )

    # Add index on system_version
    op.create_index(
        "ix_risk_assessments_system_version",
        "risk_assessments",
        ["system_version"],
    )


def downgrade() -> None:
    # ========== risk_assessments ==========
    # Drop indexes
    op.drop_index("ix_risk_assessments_system_version", table_name="risk_assessments")

    # Drop new unique constraint
    op.drop_constraint(
        "uq_risk_assessments_product_system_version",
        "risk_assessments",
        type_="unique",
    )

    # Rename user_version back to version_label (copy values first)
    op.add_column("risk_assessments", sa.Column("version_label_temp", sa.String(100)))
    op.execute("""
        UPDATE risk_assessments
        SET version_label_temp = user_version
    """)
    op.drop_column("risk_assessments", "user_version")
    op.alter_column(
        "risk_assessments",
        "version_label_temp",
        new_column_name="version_label",
    )

    # Drop system_version column
    op.drop_column("risk_assessments", "system_version")

    # Recreate old unique constraint
    op.create_unique_constraint(
        "uq_risk_assessments_product_version_label",
        "risk_assessments",
        ["product_id", "version_label"],
    )

    # ========== product_releases ==========
    # Drop indexes
    op.drop_index(
        "ix_product_releases_system_version", table_name="product_releases"
    )

    # Drop new unique constraint
    op.drop_constraint(
        "uq_product_releases_product_system_version",
        "product_releases",
        type_="unique",
    )

    # Rename user_version back to version (copy values first)
    op.add_column("product_releases", sa.Column("version_temp", sa.String(100)))
    op.execute("""
        UPDATE product_releases
        SET version_temp = user_version
    """)
    op.drop_column("product_releases", "user_version")
    op.alter_column(
        "product_releases",
        "version_temp",
        new_column_name="version",
    )

    # Drop system_version column
    op.drop_column("product_releases", "system_version")

    # Recreate old unique constraint
    op.create_unique_constraint(
        "uq_product_releases_product_version",
        "product_releases",
        ["product_id", "version"],
    )
