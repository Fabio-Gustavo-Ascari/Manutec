from datetime import datetime
from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from assistencia_manager.infrastructure.database.base import Base

class UserModel(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    username: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True)
    role: Mapped[str] = mapped_column(String(30), nullable=False)
    permissions: Mapped[str] = mapped_column(Text, nullable=False, default="")
    password_hash: Mapped[str] = mapped_column(String(300), nullable=False)
    active: Mapped[bool] = mapped_column(nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

class AuditLogModel(Base):
    __tablename__ = "audit_logs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str | None] = mapped_column(String(36), index=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    module: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    entity_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    entity_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    details: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
