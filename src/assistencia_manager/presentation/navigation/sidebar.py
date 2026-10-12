from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QVBoxLayout, QWidget


class Sidebar(QWidget):
    page_selected = Signal(int)

    def __init__(self, page_definitions: tuple[tuple[str, str], ...]) -> None:
        super().__init__()
        self.setObjectName("sidebar")
        self.setFixedWidth(240)
        self.navigation = QListWidget()
        self.navigation.setObjectName("navigation")
        for title, _description in page_definitions:
            self.navigation.addItem(QListWidgetItem(title))
        self.navigation.currentRowChanged.connect(self.page_selected)
        self.navigation.setCurrentRow(0)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.addWidget(self.navigation)
