from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QScrollArea

from assistencia_manager.infrastructure.release import ReleaseGate
from assistencia_manager.presentation.main_window import MainWindow
from assistencia_manager.presentation.pages import PAGE_DEFINITIONS
from assistencia_manager.presentation.pages.dashboard import DashboardPage
from assistencia_manager.presentation.shell import PageShell


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_every_page_uses_the_approved_shell_inside_a_responsive_viewport():
    app = _app()
    window = MainWindow()
    window.resize(1024, 640)
    window.show()
    app.processEvents()

    assert isinstance(window.content_scroll, QScrollArea)
    assert window.content_scroll.widgetResizable()
    assert window.content_scroll.horizontalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAsNeeded
    assert window.content_scroll.verticalScrollBarPolicy() == Qt.ScrollBarPolicy.ScrollBarAsNeeded
    assert tuple(window.page_by_title) == tuple(title for title, _ in PAGE_DEFINITIONS)
    for title, page in window.page_by_title.items():
        assert isinstance(page, PageShell) or page.findChild(PageShell) is not None, title

    window.close()


def test_release_gate_covers_the_complete_navigation_and_responsive_shell():
    from pathlib import Path

    project_root = Path(__file__).resolve().parents[2]
    report = ReleaseGate(project_root).run()

    assert report.ok, report.failures
    assert {"complete-navigation", "responsive-shell"} <= {
        check.name for check in report.checks
    }
    assert all(title in report.details["complete-navigation"] for title, _ in PAGE_DEFINITIONS)


def test_dashboard_quick_actions_request_navigation_to_operational_pages():
    _app()
    page = DashboardPage()
    requested = []
    page.navigation_requested.connect(requested.append)

    buttons = {button.text(): button for button in page.findChildren(__import__("PySide6.QtWidgets", fromlist=["QPushButton"]).QPushButton)}
    buttons["Nova ordem de serviço"].click()
    buttons["Registrar venda"].click()
    buttons["Repor estoque"].click()

    assert requested == ["Ordens de serviço", "Vendas", "Estoque"]
    page.close()
