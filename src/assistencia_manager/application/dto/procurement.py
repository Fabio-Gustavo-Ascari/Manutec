from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from assistencia_manager.domain.identifiers import EntityId


@dataclass(frozen=True, slots=True)
class CreatePurchaseOrderCommand:
    supplier_id: EntityId
    lines: tuple[tuple[EntityId, Decimal, Decimal], ...]
    due_date: date | None = None
    notes: str | None = None


@dataclass(frozen=True, slots=True)
class PurchaseReceiptLineCommand:
    part_id: EntityId
    quantity: Decimal


@dataclass(frozen=True, slots=True)
class ReceivePurchaseOrderCommand:
    purchase_order_id: EntityId
    lines: tuple[PurchaseReceiptLineCommand, ...]


@dataclass(frozen=True, slots=True)
class StockCountCommand:
    part_id: EntityId
    counted_quantity: Decimal
    note: str = "contagem de estoque"
