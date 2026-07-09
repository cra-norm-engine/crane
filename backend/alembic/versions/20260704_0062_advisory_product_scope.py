"""security advisory: product-scoped + many affected releases (advisory_releases)

Revision ID: 20260704_0062
Revises: 20260703_0061
Create Date: 2026-07-04 00:00:00

Re-models SecurityAdvisory from a single required product_release_id into a
product-scoped advisory (product_id) that links to many affected releases via a
new advisory_releases join table. Data-preserving: existing advisories keep
their product (derived from the old release) and get one join row for that
release.
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260704_0062"
down_revision = "20260703_0061"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add product_id (nullable first, so we can backfill before enforcing).
    op.add_column(
        "security_advisories",
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    # 2. Backfill product_id from each advisory's current release's product.
    op.execute(
        """
        UPDATE security_advisories AS sa
        SET product_id = pr.product_id
        FROM product_releases AS pr
        WHERE sa.product_release_id = pr.id
        """
    )
    # 3. Enforce + index + FK now that every row has a product.
    op.alter_column("security_advisories", "product_id", nullable=False)
    op.create_index(
        "ix_security_advisories_product_id", "security_advisories", ["product_id"]
    )
    op.create_foreign_key(
        "fk_security_advisories_product_id",
        "security_advisories",
        "products",
        ["product_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # 4. Create the advisory_releases join table.
    op.create_table(
        "advisory_releases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "security_advisory_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("security_advisories.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "product_release_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("product_releases.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.UniqueConstraint(
            "security_advisory_id", "product_release_id", name="uq_advisory_release"
        ),
    )

    # 5. Backfill: one link per existing advisory (its old single release).
    op.execute(
        """
        INSERT INTO advisory_releases
            (id, security_advisory_id, product_release_id, created_at, updated_at)
        SELECT gen_random_uuid(), id, product_release_id, now(), now()
        FROM security_advisories
        """
    )

    # 6. Drop the old single-release column (replaced by the join table).
    op.drop_column("security_advisories", "product_release_id")


def downgrade() -> None:
    # Recreate the single-release column (nullable first for backfill).
    op.add_column(
        "security_advisories",
        sa.Column("product_release_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    # Restore a single release per advisory from the earliest join row.
    op.execute(
        """
        UPDATE security_advisories AS sa
        SET product_release_id = ar.product_release_id
        FROM (
            SELECT DISTINCT ON (security_advisory_id)
                security_advisory_id, product_release_id
            FROM advisory_releases
            ORDER BY security_advisory_id, created_at
        ) AS ar
        WHERE sa.id = ar.security_advisory_id
        """
    )
    op.alter_column("security_advisories", "product_release_id", nullable=False)
    op.create_index(
        "ix_security_advisories_product_release_id",
        "security_advisories",
        ["product_release_id"],
    )
    op.create_foreign_key(
        "fk_security_advisories_product_release_id",
        "security_advisories",
        "product_releases",
        ["product_release_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.drop_table("advisory_releases")

    op.drop_constraint(
        "fk_security_advisories_product_id", "security_advisories", type_="foreignkey"
    )
    op.drop_index("ix_security_advisories_product_id", "security_advisories")
    op.drop_column("security_advisories", "product_id")
