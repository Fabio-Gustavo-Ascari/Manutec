"""Add parts, inventory movements and reservations."""

from alembic import op
import sqlalchemy as sa

revision = "0004_inventory"
down_revision = "0003_work_orders"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "parts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("category", sa.String(120), nullable=False),
        sa.Column("unit", sa.String(20), nullable=False),
        sa.Column("sku", sa.String(80), nullable=True, unique=True),
        sa.Column("cost", sa.Numeric(12, 2), nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("minimum_stock", sa.Numeric(14, 4), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
    )
    op.create_index("ix_parts_name", "parts", ["name"])
    op.create_index("ix_parts_category", "parts", ["category"])
    op.create_index("ix_parts_status", "parts", ["status"])

    op.create_table(
        "inventory_movements",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("part_id", sa.String(36), nullable=False),
        sa.Column("movement_type", sa.String(30), nullable=False),
        sa.Column("quantity", sa.Numeric(14, 4), nullable=False),
        sa.Column("reference_id", sa.String(36), nullable=True),
        sa.Column("note", sa.String(1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["part_id"], ["parts.id"]),
    )
    op.create_index("ix_inventory_movements_part_id", "inventory_movements", ["part_id"])
    op.create_index("ix_inventory_movements_movement_type", "inventory_movements", ["movement_type"])
    op.create_index("ix_inventory_movements_reference_id", "inventory_movements", ["reference_id"])

    op.create_table(
        "part_reservations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("part_id", sa.String(36), nullable=False),
        sa.Column("work_order_id", sa.String(36), nullable=False),
        sa.Column("quantity", sa.Numeric(14, 4), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["part_id"], ["parts.id"]),
        sa.ForeignKeyConstraint(["work_order_id"], ["work_orders.id"]),
    )
    op.create_index("ix_part_reservations_part_id", "part_reservations", ["part_id"])
    op.create_index("ix_part_reservations_work_order_id", "part_reservations", ["work_order_id"])
    op.create_index("ix_part_reservations_status", "part_reservations", ["status"])


def downgrade() -> None:
    op.drop_index("ix_part_reservations_status", table_name="part_reservations")
    op.drop_index("ix_part_reservations_work_order_id", table_name="part_reservations")
    op.drop_index("ix_part_reservations_part_id", table_name="part_reservations")
    op.drop_table("part_reservations")
    op.drop_index("ix_inventory_movements_reference_id", table_name="inventory_movements")
    op.drop_index("ix_inventory_movements_movement_type", table_name="inventory_movements")
    op.drop_index("ix_inventory_movements_part_id", table_name="inventory_movements")
    op.drop_table("inventory_movements")
    op.drop_index("ix_parts_status", table_name="parts")
    op.drop_index("ix_parts_category", table_name="parts")
    op.drop_index("ix_parts_name", table_name="parts")
    op.drop_table("parts")
