"""Add E14 purchase orders and stock maximum."""
from alembic import op
import sqlalchemy as sa

revision = "0011_e14_procurement"
down_revision = "0010_e13_sales_2"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column("parts", sa.Column("maximum_stock", sa.Numeric(14, 4), nullable=False, server_default="0"))
    op.create_table("purchase_orders",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("supplier_id", sa.String(36), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_purchase_orders_supplier_id", "purchase_orders", ["supplier_id"])
    op.create_index("ix_purchase_orders_status", "purchase_orders", ["status"])
    op.create_table("purchase_order_lines",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("purchase_order_id", sa.String(36), sa.ForeignKey("purchase_orders.id"), nullable=False),
        sa.Column("part_id", sa.String(36), sa.ForeignKey("parts.id"), nullable=False),
        sa.Column("ordered_quantity", sa.Numeric(14, 4), nullable=False),
        sa.Column("received_quantity", sa.Numeric(14, 4), nullable=False),
        sa.Column("unit_cost", sa.Numeric(12, 2), nullable=False))
    op.create_index("ix_purchase_order_lines_purchase_order_id", "purchase_order_lines", ["purchase_order_id"])
    op.create_index("ix_purchase_order_lines_part_id", "purchase_order_lines", ["part_id"])

def downgrade() -> None:
    op.drop_index("ix_purchase_order_lines_part_id", table_name="purchase_order_lines")
    op.drop_index("ix_purchase_order_lines_purchase_order_id", table_name="purchase_order_lines")
    op.drop_table("purchase_order_lines")
    op.drop_index("ix_purchase_orders_status", table_name="purchase_orders")
    op.drop_index("ix_purchase_orders_supplier_id", table_name="purchase_orders")
    op.drop_table("purchase_orders")
    op.drop_column("parts", "maximum_stock")
