from decimal import Decimal

import pytest

from assistencia_manager.application.dto.inventory import (
    CreatePartCommand, RecordInventoryMovementCommand, ReservePartCommand,
)
from assistencia_manager.application.services.inventory_service import InventoryService
from assistencia_manager.domain.entities.inventory import InventoryMovementType
from assistencia_manager.domain.exceptions import DuplicateEntityError
from assistencia_manager.domain.identifiers import EntityId


class Repo:
    def __init__(self): self.data = {}
    def add(self, entity): self.data[entity.id] = entity
    def get(self, identifier): return self.data.get(identifier)
    def list(self): return tuple(self.data.values())
    def search(self, term, active_only, offset, limit): return self.list()[offset:offset + limit]
    def count(self, term, active_only): return len(self.data)
    def exists_by_sku(self, sku): return any(item.sku == sku for item in self.data.values())
    def list_for_part(self, part_id, active_only=False):
        return tuple(item for item in self.data.values() if item.part_id == part_id and (not active_only or item.status.value == "active"))
    def list_for_work_order(self, work_order_id, active_only=False):
        return tuple(item for item in self.data.values() if item.work_order_id == work_order_id)


class Uow:
    def __init__(self):
        self.parts, self.inventory_movements, self.reservations, self.work_orders = Repo(), Repo(), Repo(), Repo()
    def __enter__(self): return self
    def __exit__(self, *args): pass


def test_inventory_service_creates_part_and_rejects_duplicate_sku():
    uow = Uow()
    service = InventoryService(lambda: uow)
    part = service.create_part(CreatePartCommand("Tela", "Display", sku="t-1", cost=10, price=20))

    assert part.sku == "T-1"
    with pytest.raises(DuplicateEntityError):
        service.create_part(CreatePartCommand("Outra", "Display", sku="T-1"))


def test_inventory_service_records_entry_and_reserves_only_available_quantity():
    uow = Uow()
    service = InventoryService(lambda: uow)
    part = service.create_part(CreatePartCommand("Cabo", "Acessórios"))
    service.record_movement(RecordInventoryMovementCommand(part.id, InventoryMovementType.ENTRY, Decimal("5")))
    order_id = EntityId.new()
    uow.work_orders.add(type("Order", (), {"id": order_id})())
    reservation = service.reserve(ReservePartCommand(part.id, order_id, Decimal("3")))

    assert reservation.quantity == Decimal("3")
    with pytest.raises(ValueError):
        service.reserve(ReservePartCommand(part.id, order_id, Decimal("3")))
