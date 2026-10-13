from decimal import Decimal
import pytest

from assistencia_manager.application.dto.sales import (
    AddSaleItemCommand, CashMovementCommand, CreateSaleCommand, OpenCashCommand,
    ReceiveWorkOrderCommand, RecordPaymentCommand,
)
from assistencia_manager.application.services.sales_service import SalesService
from assistencia_manager.application.services.inventory_service import InventoryService
from assistencia_manager.application.dto.inventory import CreatePartCommand, RecordInventoryMovementCommand
from assistencia_manager.bootstrap import initialize_database
from assistencia_manager.domain.entities.inventory import InventoryMovementType
from assistencia_manager.domain.entities.sales import PaymentMethod, PaymentStatus
from assistencia_manager.domain.exceptions import DomainValidationError
from assistencia_manager.application.dto.client import CreateClientCommand
from assistencia_manager.application.dto.equipment import CreateEquipmentCommand
from assistencia_manager.application.dto.work_order import AddWorkOrderItemCommand, OpenWorkOrderCommand
from assistencia_manager.application.services.client_service import ClientService
from assistencia_manager.application.services.equipment_service import EquipmentService
from assistencia_manager.application.services.work_order_service import WorkOrderService
from assistencia_manager.infrastructure.config.paths import AppPaths
from assistencia_manager.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


def test_sale_completion_payment_and_reversal_keep_stock_consistent(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    engine = initialize_database(AppPaths.default())
    make_uow = lambda: SqlAlchemyUnitOfWork(engine)
    inventory = InventoryService(make_uow)
    sales = SalesService(make_uow)
    part = inventory.create_part(CreatePartCommand("Cabo", "Acessórios", price=10))
    inventory.record_movement(RecordInventoryMovementCommand(part.id, InventoryMovementType.ENTRY, Decimal("3")))

    sale = sales.create(CreateSaleCommand())
    sales.add_item(AddSaleItemCommand(sale.id, "Cabo", Decimal("2"), Decimal("10"), part.id))
    sales.complete(sale.id)
    payment = sales.record_payment(RecordPaymentCommand(sale.id, Decimal("20"), PaymentMethod.PIX))
    sales.reverse_payment(payment.id)

    with SqlAlchemyUnitOfWork(engine) as uow:
        assert uow.sales.get(sale.id).status.value == "completed"
        assert uow.payments.get(payment.id).status is PaymentStatus.REVERSED
        movements = uow.inventory_movements.list_for_part(part.id)
        assert movements[-1].movement_type is InventoryMovementType.EXIT
    assert inventory.balance(part.id)[0] == Decimal("1.0000")
    engine.dispose()


def test_sale_stock_failure_is_atomic_and_cash_register_tracks_lifecycle(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    engine = initialize_database(AppPaths.default())
    make_uow = lambda: SqlAlchemyUnitOfWork(engine)
    inventory, sales = InventoryService(make_uow), SalesService(make_uow)
    part = inventory.create_part(CreatePartCommand("Cabo", "Acessórios", price=10))
    inventory.record_movement(RecordInventoryMovementCommand(part.id, InventoryMovementType.ENTRY, Decimal("1")))
    sale = sales.create(CreateSaleCommand())
    sales.add_item(AddSaleItemCommand(sale.id, "Cabo", Decimal("2"), Decimal("10"), part.id))
    with pytest.raises(DomainValidationError):
        sales.complete(sale.id)
    assert inventory.balance(part.id)[0] == Decimal("1.0000")
    assert sales.open_cash(OpenCashCommand(Decimal("100"))).balance == Decimal("100.00")
    with SqlAlchemyUnitOfWork(engine) as uow:
        register = uow.cash_registers.current_open()
    sales.move_cash(CashMovementCommand(register.id, Decimal("25"), "Sangria", "out"))
    assert sales.close_cash(register.id).balance == Decimal("75.00")
    engine.dispose()


def test_work_order_receipt_is_linked_to_order_and_obeys_amount(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    engine = initialize_database(AppPaths.default())
    make_uow = lambda: SqlAlchemyUnitOfWork(engine)
    client = ClientService(make_uow).create(CreateClientCommand(name="Cliente"))
    equipment = EquipmentService(make_uow).create(CreateEquipmentCommand(client.id, "Notebook"))
    orders = WorkOrderService(make_uow)
    order = orders.open(OpenWorkOrderCommand(client.id, equipment.id, "Não liga"))
    orders.add_item(AddWorkOrderItemCommand(order.id, "Diagnóstico", Decimal("1"), Decimal("90")))
    payment = SalesService(make_uow).receive_work_order(ReceiveWorkOrderCommand(order.id, Decimal("90"), PaymentMethod.PIX))
    with SqlAlchemyUnitOfWork(engine) as uow:
        sale = uow.sales.get(payment.sale_id)
        assert sale.work_order_id == order.id
        assert sale.remaining_amount == Decimal("0.00")
    engine.dispose()
