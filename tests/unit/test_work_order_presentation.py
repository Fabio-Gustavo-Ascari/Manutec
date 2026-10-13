import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from assistencia_manager.presentation.pages.work_orders import WorkOrdersPage


def test_work_orders_page_exposes_opening_and_filter_controls():
    application = QApplication.instance() or QApplication([])
    page = WorkOrdersPage()
    assert page.client_input is not None
    assert page.equipment_input is not None
    assert page.issue_input is not None
    assert page.status_filter.count() > 1
    page.close()
    application.quit()
