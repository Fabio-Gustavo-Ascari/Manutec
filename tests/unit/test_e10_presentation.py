import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QComboBox, QFrame, QPushButton, QTableWidget

from assistencia_manager.presentation.pages.inventory import InventoryPage
from assistencia_manager.presentation.pages.sales import SalesPage
from assistencia_manager.presentation.pages.work_orders import WorkOrdersPage
from assistencia_manager.presentation.shell import SearchableComboBox


def test_visual_foundation_exposes_tokens_and_reusable_page_components():
    app = QApplication.instance() or QApplication([])
    from assistencia_manager.presentation.shell import (
        APP_STYLE,
        DashboardMetricCard,
        EmptyState,
        AlertBanner,
        ActionBar,
        FilterBar,
        PageShell,
        VISUAL_TOKENS,
    )

    assert VISUAL_TOKENS["color.primary"]
    assert VISUAL_TOKENS["color.sidebar"] == "#0b1220"
    assert VISUAL_TOKENS["space.page"]
    assert "#" in APP_STYLE
    shell = PageShell("Título", "Contexto", actions=[QPushButton("Ação")])
    assert shell.header_layout is not None
    assert shell.title_label.text() == "Título"
    assert isinstance(DashboardMetricCard("Ordens", "12"), QFrame)
    assert isinstance(EmptyState("Nada por aqui", "Comece cadastrando um item"), QFrame)
    assert isinstance(FilterBar(), QFrame)
    assert isinstance(AlertBanner("Atenção", "Há itens abaixo do estoque mínimo"), QFrame)
    assert isinstance(ActionBar(), QFrame)


def test_dashboard_has_operational_hierarchy_and_quick_actions():
    app = QApplication.instance() or QApplication([])
    from assistencia_manager.presentation.pages.dashboard import DashboardPage

    page = DashboardPage()

    assert page.page_shell.title_label.text() == "Dashboard"
    assert page.metric_cards["orders"] is not None
    assert page.metric_cards["revenue"] is not None
    assert page.quick_actions.count() == 3
    assert page.status_summary is not None


def test_dashboard_fits_supported_minimum_viewport():
    app = QApplication.instance() or QApplication([])
    from assistencia_manager.presentation.pages.dashboard import DashboardPage

    page = DashboardPage()
    page.resize(1024, 640)
    page.show()
    app.processEvents()

    assert page.width() <= 1024


def test_searchable_combo_matches_any_text_case_insensitively():
    app = QApplication.instance() or QApplication([])
    combo = SearchableComboBox()

    assert combo.completer().completionMode() == combo.completer().CompletionMode.PopupCompletion
    assert combo.completer().filterMode() == Qt.MatchFlag.MatchContains
    assert combo.completer().caseSensitivity() == Qt.CaseSensitivity.CaseInsensitive


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
