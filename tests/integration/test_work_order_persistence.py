from decimal import Decimal

from assistencia_manager.application.dto.client import CreateClientCommand
from assistencia_manager.application.dto.equipment import CreateEquipmentCommand
from assistencia_manager.application.dto.work_order import AddWorkOrderItemCommand, OpenWorkOrderCommand
from assistencia_manager.application.services.client_service import ClientService
from assistencia_manager.application.services.equipment_service import EquipmentService
from assistencia_manager.application.services.work_order_service import WorkOrderService
from assistencia_manager.bootstrap import initialize_database
from assistencia_manager.infrastructure.config.paths import AppPaths
from assistencia_manager.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


def test_work_order_round_trip_persists_items_and_history(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    engine = initialize_database(AppPaths.default())
    client_service = ClientService(lambda: SqlAlchemyUnitOfWork(engine))
    equipment_service = EquipmentService(lambda: SqlAlchemyUnitOfWork(engine))
    order_service = WorkOrderService(lambda: SqlAlchemyUnitOfWork(engine))
    client = client_service.create(CreateClientCommand(name="Cliente"))
    equipment = equipment_service.create(CreateEquipmentCommand(client.id, "Notebook"))

    order = order_service.open(OpenWorkOrderCommand(client.id, equipment.id, "Não liga"))
    order_service.add_item(AddWorkOrderItemCommand(order.id, "Diagnóstico", Decimal("1"), Decimal("90")))
    loaded = order_service.get(order.id)

    assert loaded.total == Decimal("90.00")
    assert loaded.history[-1].event == "item_added"
    engine.dispose()
