import pytest
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from assistencia_manager.presentation.main_window import MainWindow


@pytest.fixture
def window():
    app = QApplication.instance() or QApplication([])
    # The Windows offscreen platform does not discover system fonts itself.
    font_path = Path("C:/Windows/Fonts/segoeui.ttf")
    if not QFontDatabase.families() and font_path.exists():
        QFontDatabase.addApplicationFont(str(font_path))
        app.setFont(QFont("Segoe UI", 9))
    window = MainWindow()
    window.show()
    app.processEvents()
    yield window
    window.close()


def test_home_module_buttons_open_every_destination(window):
    home = window.page_by_title["Dashboard"]
    assert {"Financeiro", "Estoque", "Ordens de serviço", "Vendas", "Clientes", "Compras"} <= set(home.module_buttons)
    for title, button in home.module_buttons.items():
        window.sidebar.select_page("Dashboard")
        QApplication.processEvents()
        window.content_scroll.ensureWidgetVisible(button)
        QApplication.processEvents()
        QTest.mouseClick(window.windowHandle(), Qt.MouseButton.LeftButton,
                         pos=button.mapTo(window, button.rect().center()))
        assert window.stack.currentWidget() is window.page_by_title[title]
        assert window.active_page_title.text() == title


def test_group_click_toggles_options_without_changing_active_page(window):
    sidebar = window.sidebar
    sidebar.select_page("Vendas")
    navigation = sidebar.navigation
    heading = navigation.item(0)
    order = navigation.item(sidebar._title_to_row["Ordens de serviço"])
    rect = navigation.visualItemRect(heading)
    QTest.mouseClick(navigation.viewport(), Qt.MouseButton.LeftButton, pos=rect.center())
    assert order.isHidden()
    assert window.stack.currentWidget() is window.page_by_title["Vendas"]
    QTest.mouseClick(navigation.viewport(), Qt.MouseButton.LeftButton, pos=rect.center())
    assert not order.isHidden()


def test_sidebar_mouse_click_opens_all_pages(window):
    navigation = window.sidebar.navigation
    for title in window.page_by_title:
        item = navigation.item(window.sidebar._title_to_row[title])
        navigation.scrollToItem(item)
        QApplication.processEvents()
        QTest.mouseClick(navigation.viewport(), Qt.MouseButton.LeftButton,
                         pos=navigation.visualItemRect(item).center())
        assert window.stack.currentWidget() is window.page_by_title[title], title


def test_home_shortcuts_fit_supported_window_sizes(window):
    for width, height in ((1024, 640), (1280, 720), (1366, 768)):
        window.resize(width, height)
        QApplication.processEvents()
        QApplication.processEvents()
        assert window.content_scroll.horizontalScrollBar().maximum() == 0
        viewport = window.content_scroll.viewport()
        home = window.page_by_title["Dashboard"]
        for title in ("Financeiro", "Estoque", "Ordens de serviço", "Vendas", "Clientes", "Compras"):
            button = home.module_buttons[title]
            assert viewport.rect().contains(button.mapTo(viewport, button.rect().topLeft()))
            assert viewport.rect().contains(button.mapTo(viewport, button.rect().bottomRight()))


def test_shortcut_reopens_collapsed_group(window):
    sidebar = window.sidebar
    heading = sidebar.navigation.item(0)
    sidebar.navigation.itemClicked.emit(heading)
    home = window.page_by_title["Dashboard"]
    home.module_buttons["Estoque"].click()
    assert window.stack.currentWidget() is window.page_by_title["Estoque"]
    assert not sidebar.navigation.currentItem().isHidden()
