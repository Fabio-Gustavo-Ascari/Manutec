from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QMainWindow, QStackedWidget, QWidget

from assistencia_manager.presentation.navigation.sidebar import Sidebar
from assistencia_manager.presentation.pages import PAGE_DEFINITIONS, PlaceholderPage


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Assistência Manager")
        self.resize(1366, 768)
        self.setMinimumSize(1024, 640)

        self.sidebar = Sidebar(PAGE_DEFINITIONS)
        self.stack = QStackedWidget()
        for title, description in PAGE_DEFINITIONS:
            self.stack.addWidget(PlaceholderPage(title, description))
        self.sidebar.page_selected.connect(self.stack.setCurrentIndex)

        central = QWidget()
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.sidebar)
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(central)
        self.statusBar().showMessage("Pronto")
