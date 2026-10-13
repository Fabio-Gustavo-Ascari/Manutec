"""Add work order deadlines for operational indicators."""
from alembic import op
import sqlalchemy as sa

revision = "0006_e06_operations"
down_revision = "0005_sales"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("work_orders", sa.Column("due_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_work_orders_due_at", "work_orders", ["due_at"])


def downgrade() -> None:
    op.drop_index("ix_work_orders_due_at", table_name="work_orders")
    op.drop_column("work_orders", "due_at")
