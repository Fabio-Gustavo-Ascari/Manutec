"""Complete part catalog fields for E11."""
from alembic import op
import sqlalchemy as sa

revision = "0008_e11_part_details"
down_revision = "0007_e11_catalogs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for column in (
        sa.Column("barcode", sa.String(80), nullable=True), sa.Column("brand", sa.String(120), nullable=True),
        sa.Column("supplier_id", sa.String(36), nullable=True), sa.Column("location", sa.String(120), nullable=True),
        sa.Column("warranty_days", sa.Integer, nullable=False, server_default="0"), sa.Column("promotional_price", sa.Numeric(12, 2), nullable=True),
    ):
        op.add_column("parts", column)
    op.create_index("uq_parts_barcode", "parts", ["barcode"], unique=True); op.create_index("ix_parts_brand", "parts", ["brand"]); op.create_index("ix_parts_supplier_id", "parts", ["supplier_id"])


def downgrade() -> None:
    op.drop_index("ix_parts_supplier_id", table_name="parts"); op.drop_index("ix_parts_brand", table_name="parts"); op.drop_index("uq_parts_barcode", table_name="parts")
    for name in ("promotional_price", "warranty_days", "location", "supplier_id", "brand", "barcode"): op.drop_column("parts", name)
