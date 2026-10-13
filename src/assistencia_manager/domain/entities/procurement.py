from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum

from assistencia_manager.domain.exceptions import DomainValidationError
from assistencia_manager.domain.identifiers import EntityId


def _positive(value: Decimal | int | str, label: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except Exception as error:
        raise DomainValidationError(f"{label} inválida") from error
    if result <= 0:
        raise DomainValidationError(f"{label} deve ser maior que zero")
    return result


def _money(value: Decimal | int | str) -> Decimal:
    try:
        result = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except Exception as error:
        raise DomainValidationError("Custo inválido") from error
    if result < 0:
        raise DomainValidationError("Custo não pode ser negativo")
    return result


class PurchaseOrderStatus(Enum):
    DRAFT = "draft"
    ORDERED = "ordered"
    PARTIALLY_RECEIVED = "partially_received"
    RECEIVED = "received"
    CANCELLED = "cancelled"


@dataclass(slots=True)
class PurchaseOrderLine:
    part_id: EntityId
    ordered_quantity: Decimal
    unit_cost: Decimal
    received_quantity: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        self.ordered_quantity = _positive(self.ordered_quantity, "Quantidade pedida")
        self.unit_cost = _money(self.unit_cost)
        self.received_quantity = Decimal(str(self.received_quantity))
        if self.received_quantity < 0 or self.received_quantity > self.ordered_quantity:
            raise DomainValidationError("Quantidade recebida fora do pedido")

    @property
    def remaining_quantity(self) -> Decimal:
        return self.ordered_quantity - self.received_quantity


@dataclass(slots=True)
class PurchaseOrder:
    supplier_id: EntityId
    lines: tuple[PurchaseOrderLine, ...]
    due_date: date | None = None
    notes: str | None = None
    status: PurchaseOrderStatus = PurchaseOrderStatus.DRAFT
    id: EntityId = field(default_factory=EntityId.new)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def create(cls, *, supplier_id: EntityId, lines: tuple[PurchaseOrderLine, ...], due_date: date | None = None, notes: str | None = None) -> "PurchaseOrder":
        if not isinstance(supplier_id, EntityId):
            raise DomainValidationError("Fornecedor inválido")
        if not lines:
            raise DomainValidationError("Pedido deve possuir itens")
        return cls(supplier_id=supplier_id, lines=tuple(lines), due_date=due_date, notes=notes.strip() if notes else None)

    @property
    def total(self) -> Decimal:
        return sum((line.ordered_quantity * line.unit_cost for line in self.lines), Decimal("0.00")).quantize(Decimal("0.01"))

    def receive(self, receipts: dict[EntityId, Decimal]) -> tuple[PurchaseOrderLine, ...]:
        if self.status is PurchaseOrderStatus.CANCELLED or self.status is PurchaseOrderStatus.RECEIVED:
            raise DomainValidationError("Pedido não aceita recebimento")
        for line in self.lines:
            quantity = Decimal(str(receipts.get(line.part_id, 0)))
            if quantity < 0 or quantity > line.remaining_quantity:
                raise DomainValidationError("Recebimento excede a quantidade pendente")
            line.received_quantity += quantity
        received = sum((line.received_quantity for line in self.lines), Decimal("0"))
        ordered = sum((line.ordered_quantity for line in self.lines), Decimal("0"))
        self.status = PurchaseOrderStatus.RECEIVED if received == ordered else PurchaseOrderStatus.PARTIALLY_RECEIVED
        return self.lines
