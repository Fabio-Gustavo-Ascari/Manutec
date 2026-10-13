"""Add operational metadata and evidence to work orders."""
from alembic import op
import sqlalchemy as sa

revision = "0009_e12_work_order_2"
down_revision = "0008_e11_part_details"
branch_labels = None
depends_on = None

def upgrade() -> None:
    for column in (
        sa.Column("priority", sa.String(20), nullable=False, server_default="normal"),
        sa.Column("technician_id", sa.String(36), nullable=True), sa.Column("warranty_days", sa.Integer, nullable=False, server_default="0"),
        sa.Column("origin", sa.String(80), nullable=False, server_default="counter"), sa.Column("checklist", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("observations", sa.String(4000), nullable=True), sa.Column("photos", sa.JSON, nullable=False, server_default="[]"),
        sa.Column("attachments", sa.JSON, nullable=False, server_default="[]"), sa.Column("report", sa.String(8000), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
    ): op.add_column("work_orders", column)
    op.create_index("ix_work_orders_priority", "work_orders", ["priority"])
    op.create_index("ix_work_orders_technician_id", "work_orders", ["technician_id"])

def downgrade() -> None:
    op.drop_index("ix_work_orders_technician_id", table_name="work_orders"); op.drop_index("ix_work_orders_priority", table_name="work_orders")
    for name in ("delivered_at", "report", "attachments", "photos", "observations", "checklist", "origin", "warranty_days", "technician_id", "priority"): op.drop_column("work_orders", name)
