"""Create client and equipment tables."""

from alembic import op
import sqlalchemy as sa


revision = "0002_client_equipment"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "clients",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("contacts", sa.JSON(), nullable=False),
        sa.Column("document", sa.String(length=50), nullable=True),
        sa.Column("address", sa.String(length=500), nullable=True),
        sa.Column("notes", sa.String(length=1000), nullable=True),
    )
    op.create_index("ix_clients_name", "clients", ["name"])
    op.create_table(
        "equipment",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("client_id", sa.String(length=36), nullable=False),
        sa.Column("equipment_type", sa.String(length=100), nullable=False),
        sa.Column("brand", sa.String(length=100), nullable=True),
        sa.Column("model", sa.String(length=100), nullable=True),
        sa.Column("serial_number", sa.String(length=100), nullable=True),
        sa.Column("accessories", sa.JSON(), nullable=False),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
    )
    op.create_index("ix_equipment_client_id", "equipment", ["client_id"])
    op.create_index("ix_equipment_serial_number", "equipment", ["serial_number"])


def downgrade() -> None:
    op.drop_index("ix_equipment_serial_number", table_name="equipment")
    op.drop_index("ix_equipment_client_id", table_name="equipment")
    op.drop_table("equipment")
    op.drop_index("ix_clients_name", table_name="clients")
    op.drop_table("clients")
