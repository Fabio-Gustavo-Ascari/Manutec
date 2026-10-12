"""Create technical application metadata table."""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "app_metadata",
        sa.Column("key", sa.String(length=100), primary_key=True),
        sa.Column("value", sa.String(length=500), nullable=False),
    )
    op.bulk_insert(
        sa.table(
            "app_metadata",
            sa.column("key", sa.String),
            sa.column("value", sa.String),
        ),
        [{"key": "schema_version", "value": "0001_initial"}],
    )


def downgrade() -> None:
    op.drop_table("app_metadata")
