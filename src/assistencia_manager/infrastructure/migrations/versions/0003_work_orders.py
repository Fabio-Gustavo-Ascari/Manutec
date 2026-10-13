"""Create work order storage."""

from alembic import op
import sqlalchemy as sa

revision = "0003_work_orders"
down_revision = "0002_client_equipment"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "work_orders",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("client_id", sa.String(36), nullable=False),
        sa.Column("equipment_id", sa.String(36), nullable=False),
        sa.Column("reported_issue", sa.String(2000), nullable=False),
        sa.Column("intake_checklist", sa.JSON(), nullable=False),
        sa.Column("diagnosis", sa.String(4000), nullable=True),
        sa.Column("notes", sa.String(4000), nullable=True),
        sa.Column("items", sa.JSON(), nullable=False),
        sa.Column("discount", sa.Numeric(12, 2), nullable=False),
        sa.Column("history", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["equipment_id"], ["equipment.id"]),
    )
    op.create_index("ix_work_orders_status", "work_orders", ["status"])
    op.create_index("ix_work_orders_client_id", "work_orders", ["client_id"])
    op.create_index("ix_work_orders_equipment_id", "work_orders", ["equipment_id"])


def downgrade() -> None:
    op.drop_index("ix_work_orders_equipment_id", table_name="work_orders")
    op.drop_index("ix_work_orders_client_id", table_name="work_orders")
    op.drop_index("ix_work_orders_status", table_name="work_orders")
    op.drop_table("work_orders")
