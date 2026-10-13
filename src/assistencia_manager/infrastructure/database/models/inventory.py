from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from assistencia_manager.infrastructure.database.base import Base


class PartModel(Base):
    __tablename__ = "parts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(80), nullable=True, unique=True)
    cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    minimum_stock: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    barcode: Mapped[str | None] = mapped_column(String(80), nullable=True, unique=True)
    brand: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    supplier_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    location: Mapped[str | None] = mapped_column(String(120), nullable=True)
    warranty_days: Mapped[int] = mapped_column(nullable=False, default=0)
    promotional_price: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)


class InventoryMovementModel(Base):
    __tablename__ = "inventory_movements"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    part_id: Mapped[str] = mapped_column(ForeignKey("parts.id"), nullable=False, index=True)
    movement_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    reference_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    note: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PartReservationModel(Base):
    __tablename__ = "part_reservations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    part_id: Mapped[str] = mapped_column(ForeignKey("parts.id"), nullable=False, index=True)
    work_order_id: Mapped[str] = mapped_column(ForeignKey("work_orders.id"), nullable=False, index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(14, 4), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
