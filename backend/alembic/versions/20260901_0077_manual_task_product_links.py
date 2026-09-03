"""replace manual task area links with optional product and release links"""
from alembic import op
import sqlalchemy as sa

revision = "20260901_0077"
down_revision = "20260901_0076"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("manual_tasks", sa.Column("product_id", sa.Uuid(), nullable=True))
    op.add_column("manual_tasks", sa.Column("product_release_id", sa.Uuid(), nullable=True))
    op.create_foreign_key("fk_manual_tasks_product", "manual_tasks", "products", ["product_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key("fk_manual_tasks_release", "manual_tasks", "product_releases", ["product_release_id"], ["id"], ondelete="SET NULL")
    op.create_index("ix_manual_tasks_product_id", "manual_tasks", ["product_id"])
    op.create_index("ix_manual_tasks_product_release_id", "manual_tasks", ["product_release_id"])
    op.drop_column("manual_tasks", "related_route")


def downgrade() -> None:
    op.add_column("manual_tasks", sa.Column("related_route", sa.String(80), nullable=True))
    op.drop_index("ix_manual_tasks_product_release_id", table_name="manual_tasks")
    op.drop_index("ix_manual_tasks_product_id", table_name="manual_tasks")
    op.drop_constraint("fk_manual_tasks_release", "manual_tasks", type_="foreignkey")
    op.drop_constraint("fk_manual_tasks_product", "manual_tasks", type_="foreignkey")
    op.drop_column("manual_tasks", "product_release_id")
    op.drop_column("manual_tasks", "product_id")
