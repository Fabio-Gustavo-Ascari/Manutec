from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QPushButton, QStackedWidget, QVBoxLayout, QWidget

from assistencia_manager.application.services.client_service import ClientService
from assistencia_manager.application.services.equipment_service import EquipmentService
from assistencia_manager.application.services.work_order_service import WorkOrderService
from assistencia_manager.application.services.inventory_service import InventoryService
from assistencia_manager.presentation.navigation.sidebar import Sidebar
from assistencia_manager.presentation.pages import PAGE_DEFINITIONS, PlaceholderPage
from assistencia_manager.presentation.pages.e22_pages import ClientsPage, EquipmentPage, CatalogsPage, PurchasesPage
from assistencia_manager.presentation.pages.work_orders import WorkOrdersPage
from assistencia_manager.presentation.pages.inventory import InventoryPage
from assistencia_manager.presentation.pages.sales import SalesPage
from assistencia_manager.presentation.pages.dashboard import DashboardPage
from assistencia_manager.presentation.pages.e23_pages import CompanySettingsPage, FinancePage, FiscalPage
from assistencia_manager.presentation.pages.reports import ReportsPage
from assistencia_manager.presentation.pages.access import AccessPage
from assistencia_manager.presentation.shell import APP_STYLE


class MainWindow(QMainWindow):
    def __init__(
        self,
        client_service: ClientService | None = None,
        equipment_service: EquipmentService | None = None,
        work_order_service: WorkOrderService | None = None,
        inventory_service: InventoryService | None = None,
        sales_service=None,
        dashboard_service=None,
        report_service=None,
        company_settings_service=None,
        catalog_service=None,
        procurement_service=None,
        finance_service=None,
        fiscal_service=None,
        access_service=None,
        audit_service=None,
    ) -> None:
        super().__init__()
        self.setStyleSheet(APP_STYLE)
        self.setWindowTitle("Manutec")
        self.resize(1366, 768)
        self.setMinimumSize(1024, 640)

        self.sidebar = Sidebar(PAGE_DEFINITIONS)
        self.stack = QStackedWidget()
        self.page_by_title = {}
        for title, description in PAGE_DEFINITIONS:
            if title == "Dashboard":
                page = DashboardPage(dashboard_service, report_service)
            elif title == "Clientes":
                page = ClientsPage(client_service)
            elif title == "Equipamentos":
                page = EquipmentPage(equipment_service)
            elif title == "Ordens de serviço":
                page = WorkOrdersPage(work_order_service, client_service, equipment_service)
            elif title == "Estoque":
                page = InventoryPage(inventory_service)
            elif title == "Vendas":
                page = SalesPage(sales_service, client_service, inventory_service)
            elif title == "Configurações":
                page = CompanySettingsPage(company_settings_service)
            elif title == "Cadastros":
                page = CatalogsPage(catalog_service)
            elif title == "Compras":
                page = PurchasesPage(procurement_service)
            elif title == "Financeiro":
                page = FinancePage(finance_service)
            elif title == "Fiscal e periféricos":
                page = FiscalPage(fiscal_service)
            elif title == "Relatórios":
                page = ReportsPage(report_service)
            elif title == "Usuários e auditoria":
                page = AccessPage(access_service, audit_service)
            else:
                page = PlaceholderPage(title, description)
            self.stack.addWidget(page)
            self.page_by_title[title] = page
        self.sidebar.page_selected.connect(self._show_page)

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.sidebar)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        content_layout.addWidget(self._build_header())
        content_layout.addWidget(self.stack, 1)
        layout.addWidget(content, 1)
        self.setCentralWidget(central)
        self.statusBar().showMessage("Pronto")
        self.dashboard_shortcut = QShortcut(QKeySequence("Ctrl+1"), self)
        self.dashboard_shortcut.activated.connect(lambda: self.sidebar.select_page("Dashboard"))
        self.sales_shortcut = QShortcut(QKeySequence("Ctrl+2"), self)
        self.sales_shortcut.activated.connect(lambda: self.sidebar.select_page("Vendas"))
        self.sidebar.select_page("Dashboard")

    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setObjectName("appHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 12, 20, 12)
        header_layout.setSpacing(12)

        identity = QVBoxLayout()
        identity.setSpacing(1)
        self.company_label = QLabel("Manutec")
        self.company_label.setObjectName("brandLabel")
        self.active_page_title = QLabel("Dashboard")
        self.active_page_title.setObjectName("contextLabel")
        identity.addWidget(self.company_label)
        identity.addWidget(self.active_page_title)
        header_layout.addLayout(identity)
        header_layout.addStretch()

        self.global_search = QLineEdit()
        self.global_search.setObjectName("globalSearch")
        self.global_search.setPlaceholderText("Buscar em qualquer tela...")
        self.global_search.setClearButtonEnabled(True)
        self.global_search.setMaximumWidth(300)
        self.global_search.returnPressed.connect(self._search_context)
        header_layout.addWidget(self.global_search)

        self.cash_status = QLabel("Caixa fechado")
        self.cash_status.setObjectName("contextLabel")
        self.user_label = QLabel("Operador")
        self.user_label.setObjectName("contextLabel")
        header_layout.addWidget(self.cash_status)
        header_layout.addWidget(self.user_label)

        self.help_button = QPushButton("Ajuda")
        self.help_button.clicked.connect(lambda: self.statusBar().showMessage("Use Ctrl+1 para o Dashboard e Ctrl+2 para Vendas."))
        self.settings_button = QPushButton("Configurações")
        self.settings_button.clicked.connect(lambda: self.sidebar.select_page("Configurações"))
        header_layout.addWidget(self.help_button)
        header_layout.addWidget(self.settings_button)
        return header

    def _show_page(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        title = next((name for name, page in self.page_by_title.items() if page is self.stack.currentWidget()), "Manutec")
        self.active_page_title.setText(title)
        self.statusBar().showMessage(f"Tela ativa: {title}")

    def _search_context(self) -> None:
        term = self.global_search.text().strip()
        self.statusBar().showMessage(f"Busca pronta: {term}" if term else "Digite um termo para buscar")
