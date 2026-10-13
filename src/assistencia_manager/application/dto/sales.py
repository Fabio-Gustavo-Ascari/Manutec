from dataclasses import dataclass
from decimal import Decimal

from assistencia_manager.domain.entities.sales import PaymentMethod
from assistencia_manager.domain.identifiers import EntityId


@dataclass(frozen=True, slots=True)
class CreateSaleCommand:
    client_id: EntityId | None = None
    work_order_id: EntityId | None = None


@dataclass(frozen=True, slots=True)
class AddSaleItemCommand:
    sale_id: EntityId
    description: str
    quantity: Decimal
    unit_price: Decimal
    part_id: EntityId | None = None


@dataclass(frozen=True, slots=True)
class RecordPaymentCommand:
    sale_id: EntityId
    amount: Decimal
    method: PaymentMethod
    installments: int = 1


@dataclass(frozen=True, slots=True)
class ReceiveWorkOrderCommand:
    work_order_id: EntityId
    amount: Decimal
    method: PaymentMethod
    installments: int = 1


@dataclass(frozen=True, slots=True)
class OpenCashCommand:
    amount: Decimal = Decimal("0.00")


@dataclass(frozen=True, slots=True)
class CashMovementCommand:
    cash_register_id: EntityId
    amount: Decimal
    description: str
    movement_type: str = "in"
