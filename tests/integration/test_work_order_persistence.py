from decimal import Decimal

from assistencia_manager.application.dto.client import CreateClientCommand
from assistencia_manager.application.dto.equipment import CreateEquipmentCommand
from assistencia_manager.application.dto.work_order import AddWorkOrderItemCommand, OpenWorkOrderCommand
from assistencia_manager.application.dto.work_order import UpdateWorkOrderDetailsCommand, WorkOrderEvidenceCommand
from assistencia_manager.domain.entities.work_order import WorkOrderPriority
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


def test_work_order_2_0_round_trip_persists_metadata_and_evidence(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path)); engine = initialize_database(AppPaths.default())
    clients = ClientService(lambda: SqlAlchemyUnitOfWork(engine)); equipment = EquipmentService(lambda: SqlAlchemyUnitOfWork(engine)); orders = WorkOrderService(lambda: SqlAlchemyUnitOfWork(engine))
    client = clients.create(CreateClientCommand(name="Cliente")); device = equipment.create(CreateEquipmentCommand(client.id, "Notebook"))
    order = orders.open(OpenWorkOrderCommand(client.id, device.id, "Não liga", priority=WorkOrderPriority.URGENT, origin="site", checklist=("Lacre",), warranty_days=30))
    orders.update_details(UpdateWorkOrderDetailsCommand(order.id, observations="Sem acessórios")); orders.add_photo(WorkOrderEvidenceCommand(order.id, "entrada.jpg")); orders.add_attachment(WorkOrderEvidenceCommand(order.id, "nota.pdf")); orders.set_report(WorkOrderEvidenceCommand(order.id, "Laudo"))
    loaded = orders.get(order.id)
    assert loaded.priority is WorkOrderPriority.URGENT and loaded.origin == "site" and loaded.warranty_days == 30
    assert loaded.photos == ("entrada.jpg",) and loaded.attachments == ("nota.pdf",) and loaded.report == "Laudo"
    engine.dispose()
