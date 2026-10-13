import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLineEdit, QListWidget

from assistencia_manager.presentation.main_window import MainWindow
from assistencia_manager.presentation.navigation.sidebar import Sidebar
from assistencia_manager.presentation.pages import PAGE_DEFINITIONS


def test_sidebar_groups_pages_by_operational_context():
    app = QApplication.instance() or QApplication([])

    sidebar = Sidebar(PAGE_DEFINITIONS)

    assert sidebar.section_labels == ["Operação", "Cadastros", "Financeiro", "Administração"]
    assert sidebar.navigation.item(0).text() == "Operação"
    assert not sidebar.navigation.item(0).flags() & Qt.ItemFlag.ItemIsSelectable
    assert "Dashboard" in sidebar.page_titles
    assert "Relatórios" in sidebar.page_titles


def test_main_window_exposes_global_context_and_search():
    app = QApplication.instance() or QApplication([])

    window = MainWindow()

    assert window.company_label.text() == "Manutec"
    assert window.user_label.text() == "Operador"
    assert window.cash_status.text() == "Caixa fechado"
    assert isinstance(window.global_search, QLineEdit)
    assert window.global_search.placeholderText()
    assert window.help_button is not None
    assert window.settings_button is not None


def test_main_window_navigation_updates_active_context_status_and_shortcut():
    app = QApplication.instance() or QApplication([])

    window = MainWindow()
    window.show()
    app.processEvents()

    window.sidebar.select_page("Vendas")
    app.processEvents()
    assert window.stack.currentWidget() is window.page_by_title["Vendas"]
    assert window.active_page_title.text() == "Vendas"
    assert "Vendas" in window.statusBar().currentMessage()

    window.global_search.setFocus()
    window.sidebar.select_page("Dashboard")
    window.dashboard_shortcut.activated.emit()
    app.processEvents()
    assert window.stack.currentWidget() is window.page_by_title["Dashboard"]
    assert window.sidebar.navigation.currentItem().text() == "Dashboard"


def test_shell_keeps_content_inside_supported_minimum_viewport():
    app = QApplication.instance() or QApplication([])

    window = MainWindow()
    window.resize(1024, 640)
    window.show()
    app.processEvents()

    assert window.width() <= 1024
    assert window.minimumWidth() <= 1024
    assert window.sidebar.width() <= 240
