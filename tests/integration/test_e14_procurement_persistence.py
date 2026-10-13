from decimal import Decimal

from assistencia_manager.application.dto.inventory import CreatePartCommand
from assistencia_manager.application.dto.procurement import CreatePurchaseOrderCommand, PurchaseReceiptLineCommand, ReceivePurchaseOrderCommand
from assistencia_manager.application.services.inventory_service import InventoryService
from assistencia_manager.application.services.procurement_service import ProcurementService
from assistencia_manager.bootstrap import initialize_database
from assistencia_manager.domain.identifiers import EntityId
from assistencia_manager.infrastructure.config.paths import AppPaths
from assistencia_manager.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


def test_purchase_order_round_trip_and_receipt_enters_stock(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    engine = initialize_database(AppPaths.default())
    make_uow = lambda: SqlAlchemyUnitOfWork(engine)
    inventory = InventoryService(make_uow)
    part = inventory.create_part(CreatePartCommand("Tela", "Display", cost=10, price=20, minimum_stock=2, maximum_stock=8))
    procurement = ProcurementService(make_uow)
    order = procurement.create_order(CreatePurchaseOrderCommand(EntityId.new(), ((part.id, Decimal("5"), Decimal("8")),)))
    received = procurement.receive(ReceivePurchaseOrderCommand(order.id, (PurchaseReceiptLineCommand(part.id, Decimal("5")),)))

    assert received.status.value == "received"
    assert inventory.balance(part.id)[0] == Decimal("5.0000")
    assert inventory.get(part.id).cost == Decimal("8.00")
    with SqlAlchemyUnitOfWork(engine) as uow:
        assert uow.purchase_orders.get(order.id).lines[0].received_quantity == Decimal("5.0000")
    engine.dispose()
