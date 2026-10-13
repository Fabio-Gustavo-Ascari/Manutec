from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from datetime import datetime, timezone
from decimal import Decimal

from assistencia_manager.application.dto.dashboard import DashboardSnapshot
from assistencia_manager.domain.entities.inventory import StockLedger
from assistencia_manager.domain.entities.sales import PaymentStatus, SaleStatus
from assistencia_manager.domain.entities.finance import FinancialEntryStatus, FinancialEntryType


class DashboardService:
    def __init__(self, unit_of_work_factory: Callable[[], object]) -> None:
        self._unit_of_work_factory = unit_of_work_factory

    def snapshot(self, *, now: datetime | None = None) -> DashboardSnapshot:
        current = now or datetime.now(timezone.utc)
        with self._unit_of_work_factory() as uow:
            orders = tuple(uow.work_orders.list())
            parts = tuple(uow.parts.list())
            movements = tuple(uow.inventory_movements.list())
            sales = tuple(getattr(uow.sales, "list", lambda: ())())
            payments = tuple(getattr(uow.payments, "list", lambda: ())())
            counts = Counter(order.status.value for order in orders)
            overdue = sum(
                1 for order in orders
                if order.due_at is not None
                and order.due_at < current
                and order.status.value not in {"completed", "delivered", "rejected", "cancelled"}
            )
            paid = sum(
                (payment.amount for payment in payments if payment.status is PaymentStatus.PAID),
                Decimal("0.00"),
            )
            if not payments:
                paid = sum(
                    (sale.paid_amount for sale in sales if sale.status is SaleStatus.COMPLETED),
                    Decimal("0.00"),
                )
            low_stock = 0
            for part in parts:
                balance = StockLedger(tuple(m for m in movements if m.part_id == part.id)).physical_balance(part.id)
                if balance <= part.minimum_stock:
                    low_stock += 1
            entries = tuple(getattr(uow, "financial_entries", object()).list()) if hasattr(getattr(uow, "financial_entries", None), "list") else ()
            open_payables = sum((entry.remaining_amount for entry in entries if entry.entry_type is FinancialEntryType.PAYABLE and entry.status in {FinancialEntryStatus.OPEN, FinancialEntryStatus.PARTIAL}), Decimal("0.00"))
            open_receivables = sum((entry.remaining_amount for entry in entries if entry.entry_type is FinancialEntryType.RECEIVABLE and entry.status in {FinancialEntryStatus.OPEN, FinancialEntryStatus.PARTIAL}), Decimal("0.00"))
            return DashboardSnapshot(dict(counts), overdue, paid.quantize(Decimal("0.01")), low_stock, open_payables, open_receivables)
