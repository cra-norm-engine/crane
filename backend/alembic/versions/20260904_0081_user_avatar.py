"""add user avatar data"""
import sqlalchemy as sa
from alembic import op

revision = "20260904_0081"
down_revision = "20260904_0080"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("users", sa.Column("avatar_data", sa.Text(), nullable=True))

def downgrade() -> None:
    op.drop_column("users", "avatar_data")
