from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import Date, DateTime, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from assistencia_manager.infrastructure.database.base import Base


class FinancialEntryModel(Base):
    __tablename__ = "financial_entries"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    entry_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    cost_center: Mapped[str | None] = mapped_column(String(100), nullable=True, index=True)
    source_type: Mapped[str | None] = mapped_column(String(30), nullable=True, index=True)
    source_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    paid_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RecurringExpenseModel(Base):
    __tablename__ = "recurring_expenses"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    due_day: Mapped[int] = mapped_column(nullable=False)
    category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    cost_center: Mapped[str | None] = mapped_column(String(100), nullable=True)
    active: Mapped[bool] = mapped_column(nullable=False)


class CommissionModel(Base):
    __tablename__ = "commissions"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    seller_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    sale_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    base_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    percentage: Mapped[Decimal] = mapped_column(Numeric(7, 3), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
