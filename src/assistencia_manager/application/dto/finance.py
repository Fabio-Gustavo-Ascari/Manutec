from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from assistencia_manager.domain.entities.finance import FinancialEntryType


@dataclass(frozen=True, slots=True)
class CreateFinancialEntryCommand:
    entry_type: FinancialEntryType
    description: str
    amount: Decimal
    due_date: date
    category: str | None = None
    cost_center: str | None = None
    source_type: str | None = None
    source_id: object | None = None


@dataclass(frozen=True, slots=True)
class CreateRecurringExpenseCommand:
    description: str
    amount: Decimal
    due_day: int
    category: str | None = None
    cost_center: str | None = None


@dataclass(frozen=True, slots=True)
class RecordCommissionCommand:
    seller_id: object
    sale_id: object
    base_amount: Decimal
    percentage: Decimal
