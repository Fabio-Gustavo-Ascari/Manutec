from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class DashboardSnapshot:
    orders_by_status: dict[str, int] = field(default_factory=dict)
    overdue_orders: int = 0
    received_revenue: Decimal = Decimal("0.00")
    low_stock_parts: int = 0
    open_payables: Decimal = Decimal("0.00")
    open_receivables: Decimal = Decimal("0.00")
