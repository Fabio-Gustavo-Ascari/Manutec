import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QComboBox, QTableWidget

from assistencia_manager.presentation.pages.inventory import InventoryPage
from assistencia_manager.presentation.pages.sales import SalesPage
from assistencia_manager.presentation.pages.work_orders import WorkOrdersPage


def test_work_order_redesign_uses_searchable_selections_and_detail_table():
    app = QApplication.instance() or QApplication([])
    page = WorkOrdersPage()

    assert isinstance(page.client_input, QComboBox)
    assert isinstance(page.equipment_input, QComboBox)
    assert isinstance(page.items_table, QTableWidget)
    assert page.client_input.isEditable()
    assert "UUID" not in page.client_label.text()


def test_sales_redesign_has_cart_customer_payment_and_change_controls():
    app = QApplication.instance() or QApplication([])
    page = SalesPage()

    assert isinstance(page.items_table, QTableWidget)
    assert isinstance(page.client_input, QComboBox)
    assert page.discount_input is not None
    assert page.received_input is not None
    assert page.payment_method.currentData() is not None
    assert page.change_label is not None


def test_inventory_redesign_has_catalog_table_balance_and_movement_controls():
    app = QApplication.instance() or QApplication([])
    page = InventoryPage()

    assert isinstance(page.parts_table, QTableWidget)
    assert page.movement_type is not None
    assert page.balance_label is not None
    assert page.search_input.placeholderText()
