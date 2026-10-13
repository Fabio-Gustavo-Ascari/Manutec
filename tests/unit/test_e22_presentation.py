from __future__ import annotations

import os
from decimal import Decimal
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from assistencia_manager.application.dto.pagination import Page
from assistencia_manager.domain.entities.catalog import CatalogType
from assistencia_manager.domain.entities.procurement import PurchaseOrderStatus
from assistencia_manager.domain.identifiers import EntityId
from assistencia_manager.presentation.pages.e22_pages import (
    CatalogsPage,
    ClientsPage,
    EquipmentPage,
    PurchasesPage,
)
from assistencia_manager.application.services.procurement_service import ProcurementService


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_clients_workspace_shows_summary_filter_and_contextual_detail():
    _app()
    client = SimpleNamespace(id=EntityId.new(), name="Ana", document="123", status=SimpleNamespace(value="active"), contacts=())

    class Service:
        def search(self, query):
            return Page(items=(client,), page=query.page, page_size=query.page_size, total_items=1)

    page = ClientsPage(Service())
    assert page.workspace_splitter.orientation() == Qt.Orientation.Horizontal
    assert set(page.metric_cards) == {"total", "active", "attention"}
    assert page.empty_state.isHidden()
    page.refresh()
    page.results_table.selectRow(0)
    assert page.empty_state.isHidden()
    assert "Ana" in page.detail_name_label.text()
    page.close()


def test_equipment_workspace_filters_and_updates_contextual_detail():
    app = _app()
    equipment = SimpleNamespace(
        id=EntityId.new(), client_id=EntityId.new(), equipment_type="Notebook",
        brand="Lenovo", model="T14", serial_number="SN-1", status=SimpleNamespace(value="active"),
    )

    class Service:
        def search(self, query):
            return Page(items=(equipment,), page=query.page, page_size=query.page_size, total_items=1)

    page = EquipmentPage(Service())
    page.refresh()
    page.results_table.selectRow(0)
    app.processEvents()
    assert page.detail_type_label.text() == "Notebook"
    assert "Lenovo" in page.detail_description_label.text()
    assert page.search_input.placeholderText() == "Buscar tipo, marca, modelo ou série..."
    page.close()


def test_catalog_workspace_switches_segments_and_saves_selected_catalog():
    _app()
    calls = []

    class Service:
        def search_catalogs(self, kind, term=None):
            return (SimpleNamespace(kind=kind, name="Acme", phone="", email=""),)

        def create_catalog(self, command):
            calls.append(command)

    page = CatalogsPage(Service())
    assert set(page.segment_buttons) == {"Peças", "Serviços", "Auxiliares"}
    page.segment_buttons["Auxiliares"].click()
    assert page.active_segment == "Auxiliares"
    page.type_input.setText("fornecedor")
    page.name_input.setText("Acme")
    page.save_button.click()
    assert calls[0].kind is CatalogType.SUPPLIER
    assert page.table.rowCount() == 1
    page.close()


def test_purchases_workspace_renders_status_totals_and_receives_selected_order():
    _app()
    order = SimpleNamespace(
        id=EntityId.new(), supplier_id=EntityId.new(), status=PurchaseOrderStatus.PARTIALLY_RECEIVED,
        lines=(SimpleNamespace(part_id=EntityId.new(), ordered_quantity=Decimal("5"), received_quantity=Decimal("2"), unit_cost=Decimal("10")),),
        total=Decimal("50.00"),
    )
    received = []

    class Service:
        def list_orders(self, status=None):
            return (order,)

        def receive(self, command):
            received.append(command)
            return order

        def reorder_suggestions(self):
            return ()

    page = PurchasesPage(Service())
    assert set(page.metric_cards) == {"open", "partial", "value"}
    assert page.orders_table.rowCount() == 1
    page.orders_table.selectRow(0)
    page.receipt_quantity_input.setText("3")
    page.receive_button.click()
    assert received[0].purchase_order_id == order.id
    assert received[0].lines[0].quantity == Decimal("3")
    assert "recebimento" in page.message_label.text().lower()
    page.close()


def test_procurement_service_exposes_orders_for_the_purchasing_workspace():
    orders = (SimpleNamespace(id="order-1"),)

    class Uow:
        def __enter__(self):
            self.purchase_orders = SimpleNamespace(list=lambda: orders)
            return self

        def __exit__(self, *args):
            return False

    assert ProcurementService(lambda: Uow()).list_orders() == orders
