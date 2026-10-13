"""Add E13 commercial links to sales."""
from alembic import op
import sqlalchemy as sa

revision = "0010_e13_sales_2"
down_revision = "0009_e12_work_order_2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sales", sa.Column("seller_id", sa.String(36), nullable=True))
    op.add_column("sales", sa.Column("quote_id", sa.String(36), nullable=True))
    op.create_index("ix_sales_seller_id", "sales", ["seller_id"])
    op.create_index("ix_sales_quote_id", "sales", ["quote_id"])


def downgrade() -> None:
    op.drop_index("ix_sales_quote_id", table_name="sales")
    op.drop_index("ix_sales_seller_id", table_name="sales")
    op.drop_column("sales", "quote_id")
    op.drop_column("sales", "seller_id")
