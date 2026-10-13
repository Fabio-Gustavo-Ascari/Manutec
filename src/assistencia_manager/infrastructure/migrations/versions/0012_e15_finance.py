"""Add E15 financial entries, recurring expenses and commissions."""
from alembic import op
import sqlalchemy as sa

revision = "0012_e15_finance"
down_revision = "0011_e14_procurement"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("financial_entries",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("entry_type", sa.String(20), nullable=False),
        sa.Column("description", sa.String(500), nullable=False), sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False), sa.Column("category", sa.String(100)), sa.Column("cost_center", sa.String(100)),
        sa.Column("source_type", sa.String(30)), sa.Column("source_id", sa.String(36)), sa.Column("paid_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("paid_date", sa.Date()), sa.Column("status", sa.String(20), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    for column in ("entry_type", "due_date", "category", "cost_center", "source_type", "source_id", "status"):
        op.create_index(f"ix_financial_entries_{column}", "financial_entries", [column])
    op.create_table("recurring_expenses",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("description", sa.String(500), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False), sa.Column("due_day", sa.Integer(), nullable=False),
        sa.Column("category", sa.String(100)), sa.Column("cost_center", sa.String(100)), sa.Column("active", sa.Boolean(), nullable=False))
    op.create_table("commissions",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("seller_id", sa.String(36), nullable=False),
        sa.Column("sale_id", sa.String(36), nullable=False), sa.Column("base_amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("percentage", sa.Numeric(7, 3), nullable=False), sa.Column("amount", sa.Numeric(12, 2), nullable=False))
    op.create_index("ix_commissions_seller_id", "commissions", ["seller_id"])
    op.create_index("ix_commissions_sale_id", "commissions", ["sale_id"])

def downgrade() -> None:
    op.drop_index("ix_commissions_sale_id", table_name="commissions"); op.drop_index("ix_commissions_seller_id", table_name="commissions"); op.drop_table("commissions")
    op.drop_table("recurring_expenses")
    for column in ("status", "source_id", "source_type", "cost_center", "category", "due_date", "entry_type"):
        op.drop_index(f"ix_financial_entries_{column}", table_name="financial_entries")
    op.drop_table("financial_entries")
