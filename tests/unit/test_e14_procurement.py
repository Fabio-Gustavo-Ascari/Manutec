from decimal import Decimal

import pytest

from assistencia_manager.application.dto.procurement import (
    CreatePurchaseOrderCommand,
    PurchaseReceiptLineCommand,
    ReceivePurchaseOrderCommand,
    StockCountCommand,
)
from assistencia_manager.application.services.procurement_service import ProcurementService
from assistencia_manager.domain.entities.inventory import InventoryMovementType, Part
from assistencia_manager.domain.entities.procurement import PurchaseOrderStatus
from assistencia_manager.domain.identifiers import EntityId


class Repo:
    def __init__(self):
        self.data = {}

    def add(self, entity):
        self.data[entity.id] = entity

    def get(self, identifier):
        return self.data.get(identifier)

    def list(self):
        return tuple(self.data.values())

    def list_for_part(self, part_id):
        return tuple(item for item in self.data.values() if getattr(item, "part_id", None) == part_id)

    def list_open(self):
        return tuple(item for item in self.data.values() if item.status not in {PurchaseOrderStatus.RECEIVED, PurchaseOrderStatus.CANCELLED})


class Uow:
    def __init__(self):
        self.parts = Repo()
        self.purchase_orders = Repo()
        self.inventory_movements = Repo()
        self.reservations = Repo()
        self.catalogs = Repo()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def test_purchase_order_receives_partially_and_enters_stock():
    uow = Uow()
    part = Part.create(name="Bateria", category="Energia", unit="un", cost=10, price=25, minimum_stock=2)
    uow.parts.add(part)
    service = ProcurementService(lambda: uow)
    order = service.create_order(CreatePurchaseOrderCommand(
        supplier_id=EntityId.new(), lines=((part.id, Decimal("10"), Decimal("8")),),
    ))

    service.receive(ReceivePurchaseOrderCommand(order.id, (
        PurchaseReceiptLineCommand(part.id, Decimal("4")),
    )))

    loaded = uow.purchase_orders.get(order.id)
    assert loaded.status is PurchaseOrderStatus.PARTIALLY_RECEIVED
    assert loaded.lines[0].received_quantity == Decimal("4")
    assert uow.inventory_movements.list()[-1].movement_type is InventoryMovementType.ENTRY
    assert uow.inventory_movements.list()[-1].quantity == Decimal("4")
    assert part.cost == Decimal("8.00")


def test_inventory_count_creates_guided_adjustment_and_reorder_suggestion():
    uow = Uow()
    part = Part.create(name="Cabo", category="Acessórios", unit="un", cost=10, price=20, minimum_stock=3)
    uow.parts.add(part)
    service = ProcurementService(lambda: uow)

    result = service.count(StockCountCommand(part.id, Decimal("1"), "contagem semanal"))

    assert result.movement_type is InventoryMovementType.ADJUSTMENT_IN
    assert service.reorder_suggestions()[0].part_id == part.id

