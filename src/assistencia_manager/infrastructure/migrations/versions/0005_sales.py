"""Add sales, payments and cash registers."""
from alembic import op
import sqlalchemy as sa

revision = "0005_sales"
down_revision = "0004_inventory"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("sales",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("client_id", sa.String(36), nullable=True),
        sa.Column("work_order_id", sa.String(36), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("items", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["work_order_id"], ["work_orders.id"]),
    )
    op.create_index("ix_sales_client_id", "sales", ["client_id"])
    op.create_index("ix_sales_work_order_id", "sales", ["work_order_id"])
    op.create_index("ix_sales_status", "sales", ["status"])
    op.create_table("payments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("sale_id", sa.String(36), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("method", sa.String(20), nullable=False),
        sa.Column("installments", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.ForeignKeyConstraint(["sale_id"], ["sales.id"]),
    )
    op.create_index("ix_payments_sale_id", "payments", ["sale_id"])
    op.create_index("ix_payments_status", "payments", ["status"])
    op.create_table("cash_registers",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("opening_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("movements", sa.JSON(), nullable=False),
        sa.Column("is_open", sa.Boolean(), nullable=False),
    )
    op.create_index("ix_cash_registers_is_open", "cash_registers", ["is_open"])


def downgrade() -> None:
    op.drop_index("ix_cash_registers_is_open", table_name="cash_registers")
    op.drop_table("cash_registers")
    op.drop_index("ix_payments_status", table_name="payments")
    op.drop_index("ix_payments_sale_id", table_name="payments")
    op.drop_table("payments")
    op.drop_index("ix_sales_status", table_name="sales")
    op.drop_index("ix_sales_work_order_id", table_name="sales")
    op.drop_index("ix_sales_client_id", table_name="sales")
    op.drop_table("sales")
