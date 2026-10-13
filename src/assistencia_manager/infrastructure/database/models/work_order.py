from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from assistencia_manager.infrastructure.database.base import Base


class WorkOrderModel(Base):
    __tablename__ = "work_orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    client_id: Mapped[str] = mapped_column(ForeignKey("clients.id"), nullable=False, index=True)
    equipment_id: Mapped[str] = mapped_column(ForeignKey("equipment.id"), nullable=False, index=True)
    reported_issue: Mapped[str] = mapped_column(String(2000), nullable=False)
    intake_checklist: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    diagnosis: Mapped[str | None] = mapped_column(String(4000), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(4000), nullable=True)
    items: Mapped[list[dict]] = mapped_column(JSON, nullable=False)
    discount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    history: Mapped[list[dict]] = mapped_column(JSON, nullable=False)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    priority: Mapped[str] = mapped_column(String(20), nullable=False, server_default="normal", index=True)
    technician_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    warranty_days: Mapped[int] = mapped_column(nullable=False, server_default="0")
    origin: Mapped[str] = mapped_column(String(80), nullable=False, server_default="counter")
    checklist: Mapped[list[str]] = mapped_column(JSON, nullable=False, server_default="[]")
    observations: Mapped[str | None] = mapped_column(String(4000), nullable=True)
    photos: Mapped[list[str]] = mapped_column(JSON, nullable=False, server_default="[]")
    attachments: Mapped[list[str]] = mapped_column(JSON, nullable=False, server_default="[]")
    report: Mapped[str | None] = mapped_column(String(8000), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
