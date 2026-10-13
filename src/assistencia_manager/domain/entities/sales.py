from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum

from assistencia_manager.domain.entities.base import Entity
from assistencia_manager.domain.exceptions import DomainValidationError
from assistencia_manager.domain.identifiers import EntityId

MONEY = Decimal("0.01")


def _money(value: Decimal | int | str, name: str) -> Decimal:
    try:
        result = Decimal(str(value)).quantize(MONEY, rounding=ROUND_HALF_UP)
    except Exception as error:
        raise DomainValidationError(f"{name} deve ser válido") from error
    if result < 0:
        raise DomainValidationError(f"{name} não pode ser negativo")
    return result


def _quantity(value: Decimal | int | str) -> Decimal:
    try:
        result = Decimal(str(value))
    except Exception as error:
        raise DomainValidationError("Quantidade deve ser válida") from error
    if result <= 0:
        raise DomainValidationError("Quantidade deve ser maior que zero")
    return result


class SaleStatus(Enum):
    OPEN = "open"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PaymentMethod(Enum):
    CASH = "cash"
    DEBIT = "debit"
    CREDIT = "credit"
    CARD = "card"  # compatibilidade com vendas gravadas antes da E13
    PIX = "pix"
    TRANSFER = "transfer"


class PaymentStatus(Enum):
    PAID = "paid"
    REVERSED = "reversed"


@dataclass(frozen=True, slots=True)
class SaleItem:
    description: str
    quantity: Decimal
    unit_price: Decimal
    part_id: EntityId | None = None
    discount: Decimal = Decimal("0.00")

    @property
    def amount(self) -> Decimal:
        return max(Decimal("0.00"), (self.quantity * self.unit_price - self.discount)).quantize(MONEY, rounding=ROUND_HALF_UP)


@dataclass(eq=False, slots=True)
class Sale(Entity):
    client_id: EntityId | None = None
    seller_id: EntityId | None = None
    quote_id: EntityId | None = None
    work_order_id: EntityId | None = None
    status: SaleStatus = SaleStatus.OPEN
    items: list[SaleItem] = field(default_factory=list)
    payments: list[Payment] = field(default_factory=list, repr=False)

    @classmethod
    def create(cls, client_id: EntityId | None = None, work_order_id: EntityId | None = None,
               seller_id: EntityId | None = None, quote_id: EntityId | None = None) -> Sale:
        for value, label in ((client_id, "Cliente"), (work_order_id, "Ordem"),
                             (seller_id, "Vendedor"), (quote_id, "Orçamento")):
            if value is not None and not isinstance(value, EntityId):
                raise DomainValidationError(f"{label} da venda deve ser válido")
        return cls(client_id=client_id, seller_id=seller_id, quote_id=quote_id, work_order_id=work_order_id)

    @property
    def total(self) -> Decimal:
        return sum((item.amount for item in self.items), Decimal("0.00")).quantize(MONEY)

    @property
    def paid_amount(self) -> Decimal:
        return sum((p.amount for p in self.payments if p.status is PaymentStatus.PAID), Decimal("0.00")).quantize(MONEY)

    @property
    def remaining_amount(self) -> Decimal:
        return max(Decimal("0.00"), self.total - self.paid_amount).quantize(MONEY)

    @property
    def change(self) -> Decimal:
        return max(Decimal("0.00"), self.paid_amount - self.total).quantize(MONEY)

    def add_payment(self, payment: Payment) -> None:
        if self.status is SaleStatus.CANCELLED:
            raise DomainValidationError("Venda cancelada não aceita pagamentos")
        if payment.sale_id != self.id:
            raise DomainValidationError("Pagamento não pertence à venda")
        if payment.status is PaymentStatus.REVERSED:
            raise DomainValidationError("Pagamento estornado não pode ser registrado")
        if self.paid_amount + payment.amount > self.total and payment.method is not PaymentMethod.CASH:
            raise DomainValidationError("Pagamento supera o saldo da venda")
        self.payments.append(payment)

    def record_payment(self, *, amount: Decimal | int | str, method: PaymentMethod, installments: int = 1) -> Payment:
        payment = Payment.record(sale_id=self.id, amount=amount, method=method, installments=installments)
        self.add_payment(payment)
        return payment

    def add_item(self, *, description: str, quantity: Decimal | int | str,
                 unit_price: Decimal | int | str, part_id: EntityId | None = None,
                 discount: Decimal | int | str = 0) -> None:
        if self.status is not SaleStatus.OPEN:
            raise DomainValidationError("Venda encerrada não pode ser alterada")
        if not isinstance(description, str) or not description.strip():
            raise DomainValidationError("Descrição não pode ser vazia")
        if part_id is not None and not isinstance(part_id, EntityId):
            raise DomainValidationError("Peça da venda deve ser válida")
        price = _money(unit_price, "Preço")
        discount_value = _money(discount, "Desconto")
        if discount_value > price * _quantity(quantity):
            raise DomainValidationError("Desconto não pode superar o item")
        self.items.append(SaleItem(description.strip(), _quantity(quantity), price, part_id, discount_value))

    def update_item(self, index: int, *, quantity: Decimal | int | str, unit_price: Decimal | int | str,
                    discount: Decimal | int | str = 0) -> None:
        if self.status is not SaleStatus.OPEN:
            raise DomainValidationError("Venda encerrada não pode ser alterada")
        if not isinstance(index, int) or index < 0 or index >= len(self.items):
            raise DomainValidationError("Item da venda não encontrado")
        current = self.items[index]
        replacement = SaleItem(current.description, _quantity(quantity), _money(unit_price, "Preço"), current.part_id, _money(discount, "Desconto"))
        if replacement.discount > replacement.quantity * replacement.unit_price:
            raise DomainValidationError("Desconto não pode superar o item")
        self.items[index] = replacement

    def remove_item(self, index: int) -> None:
        if self.status is not SaleStatus.OPEN:
            raise DomainValidationError("Venda encerrada não pode ser alterada")
        if not isinstance(index, int) or index < 0 or index >= len(self.items):
            raise DomainValidationError("Item da venda não encontrado")
        self.items.pop(index)

    def complete(self) -> None:
        if self.status is not SaleStatus.OPEN:
            raise DomainValidationError("Venda não está aberta")
        if not self.items:
            raise DomainValidationError("Venda deve possuir itens")
        self.status = SaleStatus.COMPLETED

    def cancel(self) -> None:
        if self.status is SaleStatus.CANCELLED:
            raise DomainValidationError("Venda já está cancelada")
        self.status = SaleStatus.CANCELLED


@dataclass(slots=True)
class Payment:
    sale_id: EntityId
    amount: Decimal
    method: PaymentMethod
    installments: int = 1
    status: PaymentStatus = PaymentStatus.PAID
    id: EntityId = field(default_factory=EntityId.new)

    @classmethod
    def record(cls, *, sale_id: EntityId, amount: Decimal | int | str,
               method: PaymentMethod, installments: int = 1) -> Payment:
        if not isinstance(sale_id, EntityId) or not isinstance(method, PaymentMethod):
            raise DomainValidationError("Pagamento inválido")
        if installments < 1:
            raise DomainValidationError("Parcelas devem ser maiores que zero")
        value = _money(amount, "Valor do pagamento")
        if value <= 0:
            raise DomainValidationError("Valor do pagamento deve ser maior que zero")
        return cls(sale_id, value, method, installments)

    def reverse(self) -> None:
        if self.status is PaymentStatus.REVERSED:
            raise DomainValidationError("Pagamento já estornado")
        self.status = PaymentStatus.REVERSED


@dataclass(slots=True)
class CashRegister:
    opening_amount: Decimal
    movements: list[tuple[Decimal, str, str]] = field(default_factory=list)
    is_open: bool = True
    id: EntityId = field(default_factory=EntityId.new)

    @classmethod
    def opening(cls, *, amount: Decimal | int | str = 0) -> CashRegister:
        return cls(_money(amount, "Abertura do caixa"))

    @property
    def balance(self) -> Decimal:
        return (self.opening_amount + sum((amount if direction == "in" else -amount for amount, direction, _ in self.movements), Decimal("0.00"))).quantize(MONEY)

    def record(self, *, amount: Decimal | int | str, description: str, movement_type: str = "in") -> None:
        if not self.is_open:
            raise DomainValidationError("Caixa fechado não aceita movimentações")
        if not isinstance(description, str) or not description.strip():
            raise DomainValidationError("Descrição da movimentação é obrigatória")
        if movement_type not in {"in", "out"}:
            raise DomainValidationError("Tipo de movimentação inválido")
        self.movements.append((_money(amount, "Movimentação"), movement_type, description.strip()))

    def close(self) -> None:
        if not self.is_open:
            raise DomainValidationError("Caixa já está fechado")
        self.is_open = False
