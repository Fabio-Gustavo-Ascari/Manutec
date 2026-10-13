from decimal import Decimal

from assistencia_manager.application.dto.inventory import (
    CreatePartCommand, RecordInventoryMovementCommand, ReservePartCommand,
)
from assistencia_manager.application.dto.client import CreateClientCommand
from assistencia_manager.application.dto.equipment import CreateEquipmentCommand
from assistencia_manager.application.dto.work_order import AddWorkOrderItemCommand, OpenWorkOrderCommand, WorkOrderStatusCommand
from assistencia_manager.application.services.client_service import ClientService
from assistencia_manager.application.services.equipment_service import EquipmentService
from assistencia_manager.application.services.work_order_service import WorkOrderService
from assistencia_manager.application.services.inventory_service import InventoryService
from assistencia_manager.bootstrap import initialize_database
from assistencia_manager.domain.entities.inventory import InventoryMovementType, ReservationStatus
from assistencia_manager.domain.entities.work_order import WorkOrderStatus
from assistencia_manager.domain.identifiers import EntityId
from assistencia_manager.infrastructure.config.paths import AppPaths
from assistencia_manager.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


def test_inventory_round_trip_persists_part_movements_and_reservation(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    engine = initialize_database(AppPaths.default())
    service = InventoryService(lambda: SqlAlchemyUnitOfWork(engine))
    client = ClientService(lambda: SqlAlchemyUnitOfWork(engine)).create(CreateClientCommand("Cliente"))
    equipment = EquipmentService(lambda: SqlAlchemyUnitOfWork(engine)).create(CreateEquipmentCommand(client.id, "Notebook"))
    order = WorkOrderService(lambda: SqlAlchemyUnitOfWork(engine)).open(OpenWorkOrderCommand(client.id, equipment.id, "Não liga"))
    part = service.create_part(CreatePartCommand("Bateria", "Energia", sku="bat-1", cost=10, price=25))
    service.record_movement(RecordInventoryMovementCommand(part.id, InventoryMovementType.ENTRY, Decimal("4")))
    reservation = service.reserve(ReservePartCommand(part.id, order.id, Decimal("2")))

    loaded = service.get(part.id)
    with SqlAlchemyUnitOfWork(engine) as uow:
        movements = uow.inventory_movements.list_for_part(part.id)
        reservations = uow.reservations.list_for_work_order(order.id)

    assert loaded.name == "Bateria"
    assert movements[0].movement_type is InventoryMovementType.ENTRY
    assert movements[0].quantity == Decimal("4.0000")
    assert reservations[0].id == reservation.id
    engine.dispose()


def test_work_order_approval_reserves_and_execution_consumes_part_atomically(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    engine = initialize_database(AppPaths.default())
    make_uow = lambda: SqlAlchemyUnitOfWork(engine)
    client = ClientService(make_uow).create(CreateClientCommand("Cliente"))
    equipment = EquipmentService(make_uow).create(CreateEquipmentCommand(client.id, "Notebook"))
    order_service = WorkOrderService(make_uow)
    inventory = InventoryService(make_uow)
    order = order_service.open(OpenWorkOrderCommand(client.id, equipment.id, "Não liga"))
    part = inventory.create_part(CreatePartCommand("Bateria", "Energia"))
    inventory.record_movement(RecordInventoryMovementCommand(part.id, InventoryMovementType.ENTRY, Decimal("2")))
    order_service.add_item(AddWorkOrderItemCommand(order.id, "Bateria", Decimal("1"), Decimal("25"), "part", part.id))
    order_service.transition(WorkOrderStatusCommand(order.id, WorkOrderStatus.UNDER_ANALYSIS))
    order_service.transition(WorkOrderStatusCommand(order.id, WorkOrderStatus.QUOTE_SENT))
    order_service.transition(WorkOrderStatusCommand(order.id, WorkOrderStatus.APPROVED))

    with SqlAlchemyUnitOfWork(engine) as uow:
        reservations = uow.reservations.list_for_work_order(order.id)
    assert reservations[0].status is ReservationStatus.ACTIVE

    order_service.transition(WorkOrderStatusCommand(order.id, WorkOrderStatus.IN_PROGRESS))
    with SqlAlchemyUnitOfWork(engine) as uow:
        movements = uow.inventory_movements.list_for_part(part.id)
        reservations = uow.reservations.list_for_work_order(order.id)
    assert movements[-1].movement_type is InventoryMovementType.CONSUMPTION
    assert reservations[0].status is ReservationStatus.CONSUMED
    engine.dispose()
