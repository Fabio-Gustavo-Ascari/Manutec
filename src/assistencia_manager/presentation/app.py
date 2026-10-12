from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from assistencia_manager.bootstrap import initialize_database
from assistencia_manager.presentation.main_window import MainWindow


def run(argv: list[str] | None = None) -> int:
    application = QApplication(argv or sys.argv)
    application.setApplicationName("Manutec")
    application.setOrganizationName("Manutec")
    initialize_database()
    window = MainWindow()
    window.show()
    return application.exec()
