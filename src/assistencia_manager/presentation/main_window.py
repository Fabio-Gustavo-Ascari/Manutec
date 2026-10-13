from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QStackedWidget, QWidget

from assistencia_manager.application.services.client_service import ClientService
from assistencia_manager.application.services.equipment_service import EquipmentService
from assistencia_manager.application.services.work_order_service import WorkOrderService
from assistencia_manager.application.services.inventory_service import InventoryService
from assistencia_manager.presentation.navigation.sidebar import Sidebar
from assistencia_manager.presentation.pages import PAGE_DEFINITIONS, PlaceholderPage
from assistencia_manager.presentation.pages.clients import ClientsPage
from assistencia_manager.presentation.pages.equipment import EquipmentPage
from assistencia_manager.presentation.pages.work_orders import WorkOrdersPage
from assistencia_manager.presentation.pages.inventory import InventoryPage


class MainWindow(QMainWindow):
    def __init__(
        self,
        client_service: ClientService | None = None,
        equipment_service: EquipmentService | None = None,
        work_order_service: WorkOrderService | None = None,
        inventory_service: InventoryService | None = None,
    ) -> None:
        super().__init__()
        self.setWindowTitle("Manutec")
        self.resize(1366, 768)
        self.setMinimumSize(1024, 640)

        self.sidebar = Sidebar(PAGE_DEFINITIONS)
        self.stack = QStackedWidget()
        for title, description in PAGE_DEFINITIONS:
            if title == "Clientes":
                page = ClientsPage(client_service)
            elif title == "Equipamentos":
                page = EquipmentPage(equipment_service)
            elif title == "Ordens de serviço":
                page = WorkOrdersPage(work_order_service)
            elif title == "Estoque":
                page = InventoryPage(inventory_service)
            else:
                page = PlaceholderPage(title, description)
            self.stack.addWidget(page)
        self.sidebar.page_selected.connect(self.stack.setCurrentIndex)

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.sidebar)
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(central)
        self.statusBar().showMessage("Pronto")
