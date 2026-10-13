from __future__ import annotations

from decimal import Decimal
from sqlalchemy import ForeignKey, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from assistencia_manager.infrastructure.database.base import Base


class SaleModel(Base):
    __tablename__ = "sales"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    client_id: Mapped[str | None] = mapped_column(ForeignKey("clients.id"), nullable=True, index=True)
    work_order_id: Mapped[str | None] = mapped_column(ForeignKey("work_orders.id"), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    items: Mapped[list[dict]] = mapped_column(JSON, nullable=False)


class PaymentModel(Base):
    __tablename__ = "payments"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    sale_id: Mapped[str] = mapped_column(ForeignKey("sales.id"), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    method: Mapped[str] = mapped_column(String(20), nullable=False)
    installments: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)


class CashRegisterModel(Base):
    __tablename__ = "cash_registers"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    opening_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    movements: Mapped[list[dict]] = mapped_column(JSON, nullable=False)
    is_open: Mapped[bool] = mapped_column(nullable=False)
