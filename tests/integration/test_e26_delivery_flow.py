from __future__ import annotations

from datetime import date
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
from assistencia_manager.application.services.finance_service import FinanceService
from assistencia_manager.application.services.inventory_service import InventoryService
from assistencia_manager.application.services.report_service import ReportService
from assistencia_manager.application.services.sales_service import SalesService
from assistencia_manager.application.services.work_order_service import WorkOrderService
from assistencia_manager.bootstrap import initialize_database
from assistencia_manager.domain.entities.inventory import InventoryMovementType
from assistencia_manager.domain.entities.sales import PaymentMethod
from assistencia_manager.domain.entities.work_order import WorkOrderStatus
from assistencia_manager.infrastructure.config.paths import AppPaths
from assistencia_manager.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


def test_customer_to_report_delivery_flow_uses_the_real_database(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    engine = initialize_database(AppPaths.default())
    factory = lambda: SqlAlchemyUnitOfWork(engine)
    clients = ClientService(factory)
    equipment = EquipmentService(factory)
    inventory = InventoryService(factory)
    work_orders = WorkOrderService(factory)
    sales = SalesService(factory)
    finance = FinanceService(factory)
    reports = ReportService(factory)

    customer = clients.create(CreateClientCommand(name="Cliente E26"))
    device = equipment.create(CreateEquipmentCommand(customer.id, "Notebook", model="E26"))
    part = inventory.create_part(
        CreatePartCommand("Tela E26", "Displays", price=Decimal("250.00"))
    )
    inventory.record_movement(
        RecordInventoryMovementCommand(
            part.id,
            InventoryMovementType.ENTRY,
            Decimal("2"),
            note="Entrada para homologação",
        )
    )
    order = work_orders.open(
        OpenWorkOrderCommand(customer.id, device.id, "Tela quebrada")
    )
    work_orders.add_item(
        AddWorkOrderItemCommand(
            order.id,
            "Tela E26",
            Decimal("1"),
            Decimal("250.00"),
            "part",
            part.id,
        )
    )
    for status in (
        WorkOrderStatus.UNDER_ANALYSIS,
        WorkOrderStatus.QUOTE_SENT,
        WorkOrderStatus.APPROVED,
        WorkOrderStatus.IN_PROGRESS,
        WorkOrderStatus.COMPLETED,
    ):
        work_orders.transition(WorkOrderStatusCommand(order.id, status))

    register = sales.open_cash(OpenCashCommand(Decimal("50.00")))
    sale = sales.create(CreateSaleCommand(customer.id, order.id))
    sales.add_item(
        AddSaleItemCommand(
            sale.id,
            "Reparo com tela",
            Decimal("1"),
            Decimal("250.00"),
            part.id,
        )
    )
    sales.complete(sale.id)
    sales.record_payment(
        RecordPaymentCommand(sale.id, Decimal("250.00"), PaymentMethod.PIX)
    )
    closed_register = sales.close_cash(register.id)

    summary = finance.cash_flow(date.today(), date.today())
    finance_report = reports.generate("finance")
    sales_report = reports.generate("sales")

    assert inventory.balance(part.id) == (Decimal("0"), Decimal("0"))
    assert closed_register.balance == Decimal("300.00")
    assert not closed_register.is_open
    assert summary.inflow == Decimal("250.00")
    assert summary.open_receivables == Decimal("0.00")
    assert len(finance_report.rows) == 1
    assert finance_report.rows[0]["paid_amount"] == Decimal("250.00")
    assert len(sales_report.rows) == 1
    assert sales_report.rows[0]["work_order_id"] == order.id
    engine.dispose()
