"""Add local users and append-only audit log for E17."""
from alembic import op
import sqlalchemy as sa

revision = "0013_e17_access_audit"
down_revision = "0012_e15_finance"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("users", sa.Column("id", sa.String(36), primary_key=True), sa.Column("display_name", sa.String(160), nullable=False), sa.Column("username", sa.String(80), nullable=False), sa.Column("role", sa.String(30), nullable=False), sa.Column("permissions", sa.Text(), nullable=False), sa.Column("password_hash", sa.String(300), nullable=False), sa.Column("active", sa.Boolean(), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_users_username", "users", ["username"], unique=True)
    op.create_table("audit_logs", sa.Column("id", sa.String(36), primary_key=True), sa.Column("user_id", sa.String(36)), sa.Column("action", sa.String(80), nullable=False), sa.Column("module", sa.String(80), nullable=False), sa.Column("entity_type", sa.String(80)), sa.Column("entity_id", sa.String(36)), sa.Column("details", sa.String(500)), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    for column in ("user_id", "action", "module", "entity_id", "created_at"): op.create_index(f"ix_audit_logs_{column}", "audit_logs", [column])

def downgrade():
    for column in ("created_at", "entity_id", "module", "action", "user_id"): op.drop_index(f"ix_audit_logs_{column}", table_name="audit_logs")
    op.drop_table("audit_logs"); op.drop_index("ix_users_username", table_name="users"); op.drop_table("users")
