from __future__ import annotations

import os
from decimal import Decimal
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from assistencia_manager.domain.entities.sales import PaymentMethod
from assistencia_manager.domain.entities.work_order import WorkOrderStatus
from assistencia_manager.presentation.pages.inventory import InventoryPage
from assistencia_manager.presentation.pages.sales import SalesPage
from assistencia_manager.presentation.pages.work_orders import WorkOrdersPage


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_work_order_counter_workspace_selects_order_and_renders_detail():
    app = _app()
    order = SimpleNamespace(
        id="order-001",
        status=WorkOrderStatus.OPEN,
        reported_issue="Não liga",
        total=Decimal("150.00"),
        items=(
            SimpleNamespace(
                description="Diagnóstico",
                quantity=Decimal("1"),
                unit_price=Decimal("150"),
                amount=Decimal("150"),
            ),
        ),
    )

    class Service:
        def search(self, query):
            return SimpleNamespace(items=(order,))

    page = WorkOrdersPage(Service())

    assert page.workspace_splitter.orientation() == Qt.Orientation.Horizontal
    assert set(page.summary_cards) == {"total", "open", "attention"}
    assert page.empty_state.isHidden() is False
    page.orders_table.selectRow(0)
    app.processEvents()
    assert page.empty_state.isHidden()
    assert "order-00" in page.detail_order_label.text()
    assert "Aberta" in page.detail_status_label.text()
    assert page.items_table.rowCount() == 1
    page.close()


def test_pdv_workspace_updates_cart_payment_and_operational_shortcuts():
    _app()
    item = SimpleNamespace(
        description="Tela OLED",
        quantity=Decimal("1"),
        unit_price=Decimal("320"),
        amount=Decimal("300"),
    )
    sale = SimpleNamespace(id="sale-001", items=(item,), total=Decimal("300"))
    payments = []

    class Service:
        def record_payment(self, command):
            payments.append(command)
            return SimpleNamespace(amount=command.amount)

    page = SalesPage(Service())
    assert page.checkout_panel.objectName() == "checkoutPanel"
    assert page.sale_header.objectName() == "saleHeader"
    assert set(page.shortcuts) == {"new", "search", "add", "pay", "complete"}
    assert page.cart_empty_state.isHidden() is False

    page.sale = sale
    page._render_items()
    assert page.items_table.rowCount() == 1
    assert page.cart_empty_state.isHidden()
    assert "300,00" in page.total_label.text()

    page.received_input.setText("300")
    page.payment_method.setCurrentIndex(page.payment_method.findData(PaymentMethod.PIX))
    page._pay()
    assert payments[0].amount == Decimal("300")
    assert payments[0].method == PaymentMethod.PIX
    page.close()


def test_inventory_workspace_updates_indicators_and_records_selected_movement():
    app = _app()
    low_part = SimpleNamespace(
        id="part-001",
        name="Conector",
        category="Componentes",
        sku="CON-1",
        minimum_stock=Decimal("3"),
    )
    movements = []

    class Service:
        def search(self, query):
            return SimpleNamespace(items=(low_part,))

        def balance(self, identifier):
            return Decimal("2"), Decimal("2")

        def record_movement(self, command):
            movements.append(command)

    page = InventoryPage(Service())
    assert page.workspace_splitter.orientation() == Qt.Orientation.Horizontal
    assert set(page.metric_cards) == {"items", "low_stock", "physical"}
    assert page.metric_cards["low_stock"].value_label.text() == "1"
    assert page.movement_empty_state.isHidden() is False

    page.parts_table.selectRow(0)
    app.processEvents()
    assert page.movement_empty_state.isHidden()
    assert "Conector" in page.selected_part_label.text()
    page.quantity_input.setText("4")
    page._movement()
    assert movements[0].quantity == Decimal("4")
    assert str(movements[0].part_id) == "part-001"
    page.close()
