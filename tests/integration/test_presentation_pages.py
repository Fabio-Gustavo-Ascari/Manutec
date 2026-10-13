from __future__ import annotations

from PySide6.QtWidgets import QApplication

from assistencia_manager.presentation.main_window import MainWindow
from assistencia_manager.presentation.pages.clients import ClientsPage
from assistencia_manager.presentation.pages.equipment import EquipmentPage
from assistencia_manager.presentation.pages.work_orders import WorkOrdersPage
from assistencia_manager.presentation.pages.inventory import InventoryPage
from assistencia_manager.application.dto.client import ClientSearchQuery
from assistencia_manager.application.dto.equipment import EquipmentSearchQuery
from assistencia_manager.domain.entities.client import Client
from assistencia_manager.domain.entities.equipment import Equipment
from assistencia_manager.domain.identifiers import EntityId
from uuid import uuid4


def test_main_window_contains_client_and_equipment_pages():
    application = QApplication.instance() or QApplication([])

    window = MainWindow()

    assert isinstance(window.stack.widget(1), ClientsPage)
    assert isinstance(window.stack.widget(2), EquipmentPage)
    assert isinstance(window.stack.widget(3), WorkOrdersPage)
    assert isinstance(window.stack.widget(4), InventoryPage)
    assert window.sidebar.navigation.count() == window.stack.count()

    window.close()
    application.quit()


def test_client_page_can_load_search_results_into_form_and_deactivate():
    application = QApplication.instance() or QApplication([])

    class Service:
        def search(self, query):
            return type("Page", (), {"items": (Client(id=EntityId.new(), name="Ana"),), "total_items": 1, "total_pages": 1})()

        def update(self, command):
            return Client(id=command.identifier, name=command.name or "Ana")

        def deactivate(self, identifier):
            return Client(id=identifier, name="Ana")

    page = ClientsPage(Service())
    page.refresh()

    assert page.results_table.rowCount() == 1
    page.results_table.selectRow(0)
    page.load_selected()
    assert page.form.name_input.text() == "Ana"
    from PySide6.QtWidgets import QMessageBox
    QMessageBox.question = staticmethod(lambda *args: QMessageBox.StandardButton.Yes)
    page.deactivate_selected()
    assert "inativado" in page.message.text().lower()
    page.close()
    application.quit()


def test_equipment_page_can_search_and_load_selected_equipment():
    application = QApplication.instance() or QApplication([])
    client_id = EntityId(uuid4())

    class Service:
        def search(self, query):
            return type("Page", (), {"items": (Equipment(id=EntityId.new(), client_id=client_id, equipment_type="Notebook"),), "total_items": 1, "total_pages": 1})()

        def update(self, command):
            return Equipment(id=command.identifier, client_id=client_id, equipment_type=command.equipment_type or "Notebook")

        def deactivate(self, identifier):
            return Equipment(id=identifier, client_id=client_id, equipment_type="Notebook")

    page = EquipmentPage(Service())
    page.refresh()
    assert page.results_table.rowCount() == 1
    page.results_table.selectRow(0)
    page.load_selected()
    assert page.form.equipment_type_input.text() == "Notebook"
    page.close()
    application.quit()
