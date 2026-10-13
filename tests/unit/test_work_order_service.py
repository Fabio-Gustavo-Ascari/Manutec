from decimal import Decimal

import pytest

from assistencia_manager.application.dto.work_order import AddWorkOrderItemCommand, OpenWorkOrderCommand, WorkOrderStatusCommand
from assistencia_manager.application.services.work_order_service import WorkOrderService
from assistencia_manager.domain.entities.client import Client
from assistencia_manager.domain.entities.equipment import Equipment
from assistencia_manager.domain.entities.work_order import WorkOrderStatus
from assistencia_manager.domain.exceptions import EntityNotFoundError


class Repo:
    def __init__(self): self.data = {}
    def add(self, entity): self.data[entity.id] = entity
    def get(self, identifier): return self.data.get(identifier)
    def list(self): return tuple(self.data.values())
    def search(self, term, status, offset, limit): return self.list()[offset:offset + limit]
    def count(self, term, status): return len(self.data)


class Uow:
    def __init__(self):
        self.clients, self.equipment, self.work_orders = Repo(), Repo(), Repo()
    def __enter__(self): return self
    def __exit__(self, *args): pass


def test_service_opens_order_only_for_existing_client_and_equipment():
    uow = Uow()
    client = Client(name="Cliente")
    equipment = Equipment(client_id=client.id, equipment_type="Notebook")
    uow.clients.add(client)
    uow.equipment.add(equipment)
    service = WorkOrderService(lambda: uow)

    order = service.open(OpenWorkOrderCommand(client.id, equipment.id, "Não liga"))

    assert order in uow.work_orders.list()
    with pytest.raises(EntityNotFoundError):
        service.open(OpenWorkOrderCommand(client.id, equipment.id.new(), "Falha"))


def test_service_adds_item_and_transitions_order():
    uow = Uow()
    client = Client(name="Cliente")
    equipment = Equipment(client_id=client.id, equipment_type="Notebook")
    uow.clients.add(client); uow.equipment.add(equipment)
    service = WorkOrderService(lambda: uow)
    order = service.open(OpenWorkOrderCommand(client.id, equipment.id, "Não liga"))

    service.add_item(AddWorkOrderItemCommand(order.id, "Serviço", Decimal("1"), Decimal("80")))
    service.transition(WorkOrderStatusCommand(order.id, WorkOrderStatus.UNDER_ANALYSIS))

    assert order.total == Decimal("80.00")
    assert order.status is WorkOrderStatus.UNDER_ANALYSIS
