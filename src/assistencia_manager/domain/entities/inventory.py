from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum

from assistencia_manager.domain.entities.base import Entity
from assistencia_manager.domain.exceptions import DomainValidationError
from assistencia_manager.domain.identifiers import EntityId

MONEY = Decimal("0.01")


def _text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DomainValidationError(f"{name} não pode ser vazio")
    return value.strip()


def _quantity(value: Decimal | int | str, name: str = "Quantidade") -> Decimal:
    try:
        result = Decimal(str(value))
    except Exception as error:
        raise DomainValidationError(f"{name} deve ser válida") from error
    if result <= 0:
        raise DomainValidationError(f"{name} deve ser maior que zero")
    return result


def _nonnegative_quantity(value: Decimal | int | str, name: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except Exception as error:
        raise DomainValidationError(f"{name} deve ser válida") from error
    if result < 0:
        raise DomainValidationError(f"{name} não pode ser negativa")
    return result


def _money(value: Decimal | int | str, name: str) -> Decimal:
    try:
        result = Decimal(str(value)).quantize(MONEY, rounding=ROUND_HALF_UP)
    except Exception as error:
        raise DomainValidationError(f"{name} deve ser válido") from error
    if result < 0:
        raise DomainValidationError(f"{name} não pode ser negativo")
    return result


class InventoryMovementType(Enum):
    ENTRY = "entry"
    EXIT = "exit"
    ADJUSTMENT_IN = "adjustment_in"
    ADJUSTMENT_OUT = "adjustment_out"
    CONSUMPTION = "consumption"
    RETURN = "return"

    @property
    def direction(self) -> int:
        return 1 if self in {self.ENTRY, self.ADJUSTMENT_IN, self.RETURN} else -1


class ReservationStatus(Enum):
    ACTIVE = "active"
    RELEASED = "released"
    CONSUMED = "consumed"


@dataclass(eq=False, slots=True)
class Part(Entity):
    name: str = ""
    category: str = ""
    unit: str = "un"
    sku: str | None = None
    cost: Decimal = Decimal("0.00")
    price: Decimal = Decimal("0.00")
    minimum_stock: Decimal = Decimal("0")
    barcode: str | None = None
    brand: str | None = None
    supplier_id: EntityId | None = None
    location: str | None = None
    warranty_days: int = 0
    promotional_price: Decimal | None = None

    @classmethod
    def create(
        cls, *, name: str, category: str, unit: str, cost: Decimal | int | str,
        price: Decimal | int | str, minimum_stock: Decimal | int | str = 0,
        sku: str | None = None, barcode: str | None = None, brand: str | None = None,
        supplier_id: EntityId | None = None, location: str | None = None, warranty_days: int = 0,
        promotional_price: Decimal | int | str | None = None,
    ) -> Part:
        normalized_sku = sku.strip().upper() if isinstance(sku, str) and sku.strip() else None
        return cls(
            name=_text(name, "Nome"), category=_text(category, "Categoria"),
            unit=_text(unit, "Unidade"), sku=normalized_sku,
            cost=_money(cost, "Custo"), price=_money(price, "Preço"),
            minimum_stock=_nonnegative_quantity(minimum_stock, "Estoque mínimo"),
            barcode=barcode.strip() if barcode else None, brand=brand.strip() if brand else None,
            supplier_id=supplier_id, location=location.strip() if location else None,
            warranty_days=warranty_days, promotional_price=_money(promotional_price, "Preço promocional") if promotional_price is not None else None,
        )

    def __post_init__(self) -> None:
        self.name = _text(self.name, "Nome")
        self.category = _text(self.category, "Categoria")
        self.unit = _text(self.unit, "Unidade")
        self.cost = _money(self.cost, "Custo")
        self.price = _money(self.price, "Preço")
        self.minimum_stock = _nonnegative_quantity(self.minimum_stock, "Estoque mínimo")
        if self.warranty_days < 0:
            raise DomainValidationError("Garantia não pode ser negativa")
        if self.promotional_price is not None:
            self.promotional_price = _money(self.promotional_price, "Preço promocional")


@dataclass(frozen=True, slots=True)
class InventoryMovement:
    part_id: EntityId
    movement_type: InventoryMovementType
    quantity: Decimal
    reference_id: EntityId | None = None
    note: str | None = None
    id: EntityId = field(default_factory=EntityId.new)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not isinstance(self.part_id, EntityId):
            raise DomainValidationError("Movimento deve possuir peça válida")
        object.__setattr__(self, "quantity", _quantity(self.quantity))

    @property
    def signed_quantity(self) -> Decimal:
        return self.quantity * self.movement_type.direction


@dataclass(slots=True)
class PartReservation:
    part_id: EntityId
    work_order_id: EntityId
    quantity: Decimal
    status: ReservationStatus = ReservationStatus.ACTIVE
    id: EntityId = field(default_factory=EntityId.new)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @classmethod
    def reserve(cls, *, part_id: EntityId, work_order_id: EntityId, quantity: Decimal | int | str) -> PartReservation:
        return cls(part_id=part_id, work_order_id=work_order_id, quantity=_quantity(quantity))

    def release(self) -> None:
        if self.status is not ReservationStatus.ACTIVE:
            raise DomainValidationError("Reserva não está ativa")
        self.status = ReservationStatus.RELEASED

    def consume(self) -> None:
        if self.status is not ReservationStatus.ACTIVE:
            raise DomainValidationError("Reserva não está ativa")
        self.status = ReservationStatus.CONSUMED


class StockLedger:
    def __init__(self, movements: tuple[InventoryMovement, ...] = ()) -> None:
        self._movements = list(movements)

    @property
    def movements(self) -> tuple[InventoryMovement, ...]:
        return tuple(self._movements)

    def physical_balance(self, part_id: EntityId) -> Decimal:
        return sum((m.signed_quantity for m in self._movements if m.part_id == part_id), Decimal("0"))

    def available_balance(self, part_id: EntityId, reservations: tuple[PartReservation, ...] = ()) -> Decimal:
        reserved = sum((r.quantity for r in reservations if r.part_id == part_id and r.status is ReservationStatus.ACTIVE), Decimal("0"))
        return self.physical_balance(part_id) - reserved

    def record(
        self, *, part_id: EntityId, movement_type: InventoryMovementType,
        quantity: Decimal | int | str, reference_id: EntityId | None = None,
        note: str | None = None,
    ) -> InventoryMovement:
        movement = InventoryMovement(part_id, movement_type, _quantity(quantity), reference_id, note)
        if movement.signed_quantity < 0 and self.physical_balance(part_id) + movement.signed_quantity < 0:
            raise DomainValidationError("Saldo de estoque não pode ficar negativo")
        self._movements.append(movement)
        return movement
