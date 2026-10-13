from decimal import Decimal

from assistencia_manager.application.dto.client import CreateClientCommand
from assistencia_manager.application.dto.equipment import CreateEquipmentCommand
from assistencia_manager.application.dto.inventory import (
    CreatePartCommand,
    RecordInventoryMovementCommand,
)
from assistencia_manager.application.dto.sales import (
    AddSaleItemCommand,
    CreateSaleCommand,
    OpenCashCommand,
    RecordPaymentCommand,
)
from assistencia_manager.application.dto.work_order import (
    AddWorkOrderItemCommand,
    OpenWorkOrderCommand,
    WorkOrderStatusCommand,
)
from assistencia_manager.application.services.client_service import ClientService
from assistencia_manager.application.services.equipment_service import EquipmentService
from assistencia_manager.application.services.inventory_service import InventoryService
from assistencia_manager.application.services.sales_service import SalesService
from assistencia_manager.application.services.work_order_service import WorkOrderService
from assistencia_manager.bootstrap import initialize_database
from assistencia_manager.domain.entities.inventory import InventoryMovementType
from assistencia_manager.domain.entities.sales import PaymentMethod
from assistencia_manager.domain.entities.work_order import WorkOrderStatus
from assistencia_manager.infrastructure.config.paths import AppPaths
from assistencia_manager.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


def test_customer_to_warranty_flow_survives_real_database(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    engine = initialize_database(AppPaths.default())
    factory = lambda: SqlAlchemyUnitOfWork(engine)
    clients = ClientService(factory)
    equipment = EquipmentService(factory)
    inventory = InventoryService(factory)
    work_orders = WorkOrderService(factory)
    sales = SalesService(factory)

    customer = clients.create(CreateClientCommand(name="Cliente homologação"))
    device = equipment.create(CreateEquipmentCommand(customer.id, "Notebook", model="X"))
    part = inventory.create_part(CreatePartCommand("Teclado", "Periféricos", price=Decimal("80")))
    inventory.record_movement(
        RecordInventoryMovementCommand(part.id, InventoryMovementType.ENTRY, Decimal("2"), note="Compra")
    )
    order = work_orders.open(OpenWorkOrderCommand(customer.id, device.id, "Teclas falhando", warranty_days=90))
    work_orders.add_item(AddWorkOrderItemCommand(order.id, "Troca de teclado", Decimal("1"), Decimal("120")))
    work_orders.add_item(AddWorkOrderItemCommand(order.id, "Teclado", Decimal("1"), Decimal("80"), "part", part.id))
    for status in (
        WorkOrderStatus.UNDER_ANALYSIS,
        WorkOrderStatus.QUOTE_SENT,
        WorkOrderStatus.APPROVED,
        WorkOrderStatus.IN_PROGRESS,
        WorkOrderStatus.COMPLETED,
    ):
        work_orders.transition(WorkOrderStatusCommand(order.id, status))

    register = sales.open_cash(OpenCashCommand(Decimal("0")))
    sale = sales.create(CreateSaleCommand(customer.id, order.id))
    sales.add_item(AddSaleItemCommand(sale.id, "Serviço e peça", Decimal("1"), Decimal("200"), part.id))
    sales.complete(sale.id)
    payment = sales.record_payment(RecordPaymentCommand(sale.id, Decimal("200"), PaymentMethod.PIX))
    delivered = work_orders.get(order.id)
    delivered.mark_delivered()
    with factory() as uow:
        uow.work_orders.add(delivered)
    sales.close_cash(register.id)

    restored = work_orders.get(order.id)
    assert restored.status is WorkOrderStatus.DELIVERED
    assert restored.warranty_until is not None
    assert payment.amount == Decimal("200.00")
    assert inventory.balance(part.id) == (Decimal("0"), Decimal("0"))
    engine.dispose()
