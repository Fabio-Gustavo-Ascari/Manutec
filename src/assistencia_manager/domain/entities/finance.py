from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum

from assistencia_manager.domain.exceptions import DomainValidationError
from assistencia_manager.domain.identifiers import EntityId

MONEY = Decimal("0.01")


def _money(value, label="Valor"):
    try:
        result = Decimal(str(value)).quantize(MONEY, rounding=ROUND_HALF_UP)
    except Exception as error:
        raise DomainValidationError(f"{label} inválido") from error
    if result <= 0:
        raise DomainValidationError(f"{label} deve ser maior que zero")
    return result


class FinancialEntryType(Enum):
    PAYABLE = "payable"
    RECEIVABLE = "receivable"


class FinancialEntryStatus(Enum):
    OPEN = "open"
    PARTIAL = "partial"
    PAID = "paid"
    CANCELLED = "cancelled"


@dataclass(slots=True)
class FinancialEntry:
    entry_type: FinancialEntryType
    description: str
    amount: Decimal
    due_date: date
    category: str | None = None
    cost_center: str | None = None
    source_type: str | None = None
    source_id: EntityId | None = None
    paid_amount: Decimal = Decimal("0.00")
    paid_date: date | None = None
    status: FinancialEntryStatus = FinancialEntryStatus.OPEN
    id: EntityId = field(default_factory=EntityId.new)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        if not isinstance(self.entry_type, FinancialEntryType):
            raise DomainValidationError("Tipo financeiro inválido")
        if not isinstance(self.due_date, date):
            raise DomainValidationError("Vencimento inválido")
        if not isinstance(self.description, str) or not self.description.strip():
            raise DomainValidationError("Descrição financeira é obrigatória")
        self.description = self.description.strip()
        self.amount = _money(self.amount)
        self.paid_amount = Decimal(str(self.paid_amount)).quantize(MONEY)
        if self.paid_amount < 0 or self.paid_amount > self.amount:
            raise DomainValidationError("Valor pago fora do lançamento")

    @property
    def remaining_amount(self):
        return max(Decimal("0.00"), self.amount - self.paid_amount).quantize(MONEY)

    def settle(self, amount=None, paid_date: date | None = None):
        if self.status is FinancialEntryStatus.CANCELLED:
            raise DomainValidationError("Lançamento cancelado não pode ser pago")
        value = self.remaining_amount if amount is None else _money(amount, "Pagamento")
        if value > self.remaining_amount:
            raise DomainValidationError("Pagamento supera o saldo")
        self.paid_amount = (self.paid_amount + value).quantize(MONEY)
        self.paid_date = paid_date or date.today()
        self.status = FinancialEntryStatus.PAID if not self.remaining_amount else FinancialEntryStatus.PARTIAL


@dataclass(slots=True)
class RecurringExpense:
    description: str
    amount: Decimal
    due_day: int
    category: str | None = None
    cost_center: str | None = None
    active: bool = True
    id: EntityId = field(default_factory=EntityId.new)

    def __post_init__(self):
        if not self.description or not self.description.strip():
            raise DomainValidationError("Descrição da recorrência é obrigatória")
        if not 1 <= self.due_day <= 28:
            raise DomainValidationError("Dia da recorrência deve ficar entre 1 e 28")
        self.description = self.description.strip()
        self.amount = _money(self.amount)


@dataclass(slots=True)
class Commission:
    seller_id: EntityId
    sale_id: EntityId
    base_amount: Decimal
    percentage: Decimal
    amount: Decimal = field(init=False)
    id: EntityId = field(default_factory=EntityId.new)

    def __post_init__(self):
        if not isinstance(self.seller_id, EntityId) or not isinstance(self.sale_id, EntityId):
            raise DomainValidationError("Vínculo da comissão inválido")
        self.base_amount = _money(self.base_amount, "Base da comissão")
        self.percentage = Decimal(str(self.percentage))
        if self.percentage < 0 or self.percentage > 100:
            raise DomainValidationError("Percentual da comissão inválido")
        self.amount = (self.base_amount * self.percentage / Decimal("100")).quantize(MONEY, rounding=ROUND_HALF_UP)


@dataclass(frozen=True, slots=True)
class CashFlowSummary:
    start: date
    end: date
    inflow: Decimal
    outflow: Decimal
    balance: Decimal
    open_payables: Decimal
    open_receivables: Decimal
