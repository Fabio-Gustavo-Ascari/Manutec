from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from assistencia_manager.domain.entities.inventory import InventoryMovementType
from assistencia_manager.domain.identifiers import EntityId


@dataclass(frozen=True, slots=True)
class CreatePartCommand:
    name: str
    category: str
    unit: str = "un"
    sku: str | None = None
    cost: Decimal = Decimal("0.00")
    price: Decimal = Decimal("0.00")
    minimum_stock: Decimal = Decimal("0")


@dataclass(frozen=True, slots=True)
class UpdatePartCommand:
    identifier: EntityId
    name: str
    category: str
    unit: str
    cost: Decimal
    price: Decimal
    minimum_stock: Decimal


@dataclass(frozen=True, slots=True)
class PartSearchQuery:
    search: str | None = None
    active_only: bool = True
    page: int = 1
    page_size: int = 20


@dataclass(frozen=True, slots=True)
class RecordInventoryMovementCommand:
    part_id: EntityId
    movement_type: InventoryMovementType
    quantity: Decimal
    reference_id: EntityId | None = None
    note: str | None = None


@dataclass(frozen=True, slots=True)
class ReservePartCommand:
    part_id: EntityId
    work_order_id: EntityId
    quantity: Decimal
