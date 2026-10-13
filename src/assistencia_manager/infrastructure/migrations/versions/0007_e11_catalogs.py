"""Add complete operational catalogs for E11."""
from alembic import op
import sqlalchemy as sa

revision = "0007_e11_catalogs"
down_revision = "0006_e06_operations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("catalog_entries",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("kind", sa.String(30), nullable=False),
        sa.Column("name", sa.String(200), nullable=False), sa.Column("document", sa.String(40)),
        sa.Column("phone", sa.String(40)), sa.Column("email", sa.String(200)), sa.Column("notes", sa.String(1000)),
        sa.Column("status", sa.String(20), nullable=False))
    op.create_index("ix_catalog_entries_kind", "catalog_entries", ["kind"]); op.create_index("ix_catalog_entries_name", "catalog_entries", ["name"]); op.create_index("ix_catalog_entries_status", "catalog_entries", ["status"])
    op.create_table("services", sa.Column("id", sa.String(36), primary_key=True), sa.Column("name", sa.String(200), nullable=False), sa.Column("price", sa.Numeric(12, 2), nullable=False), sa.Column("warranty_days", sa.Integer, nullable=False), sa.Column("warranty_terms", sa.String(1000)), sa.Column("description", sa.String(2000)), sa.Column("status", sa.String(20), nullable=False))
    op.create_index("ix_services_name", "services", ["name"]); op.create_index("ix_services_status", "services", ["status"])
    op.create_table("service_packages", sa.Column("id", sa.String(36), primary_key=True), sa.Column("name", sa.String(200), nullable=False), sa.Column("items", sa.JSON, nullable=False), sa.Column("price", sa.Numeric(12, 2), nullable=False), sa.Column("status", sa.String(20), nullable=False))
    op.create_index("ix_service_packages_name", "service_packages", ["name"]); op.create_index("ix_service_packages_status", "service_packages", ["status"])
    op.create_table("warranty_rules", sa.Column("id", sa.String(36), primary_key=True), sa.Column("name", sa.String(200), nullable=False), sa.Column("days", sa.Integer, nullable=False), sa.Column("applies_to", sa.String(100), nullable=False), sa.Column("terms", sa.String(2000)), sa.Column("status", sa.String(20), nullable=False))
    op.create_index("ix_warranty_rules_status", "warranty_rules", ["status"])


def downgrade() -> None:
    op.drop_table("warranty_rules"); op.drop_table("service_packages"); op.drop_table("services"); op.drop_table("catalog_entries")
