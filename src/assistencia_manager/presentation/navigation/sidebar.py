from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QVBoxLayout, QWidget


class Sidebar(QWidget):
    page_selected = Signal(int)

    def __init__(self, page_definitions: tuple[tuple[str, str], ...]) -> None:
        super().__init__()
        self.setObjectName("sidebar")
        self.setMinimumWidth(196)
        self.setMaximumWidth(240)
        self.section_labels = ["Operação", "Cadastros", "Financeiro", "Administração"]
        groups = {
            "Operação": {"Dashboard", "Ordens de serviço", "Estoque", "Vendas"},
            "Cadastros": {"Clientes", "Equipamentos", "Cadastros", "Compras"},
            "Financeiro": {"Financeiro", "Fiscal e periféricos"},
            "Administração": {"Configurações", "Relatórios", "Usuários e auditoria"},
        }
        self.navigation = QListWidget()
        self.navigation.setObjectName("navigation")
        self.page_titles: list[str] = []
        self._title_to_row: dict[str, int] = {}
        self._title_to_index = {title: index for index, (title, _description) in enumerate(page_definitions)}
        for section in self.section_labels:
            heading = QListWidgetItem(section)
            heading.setData(Qt.ItemDataRole.UserRole, "section")
            heading.setFlags(Qt.ItemFlag.ItemIsEnabled)
            self.navigation.addItem(heading)
            for title, _description in page_definitions:
                if title not in groups[section]:
                    continue
                item = QListWidgetItem(title)
                item.setData(Qt.ItemDataRole.UserRole, title)
                self.navigation.addItem(item)
                self.page_titles.append(title)
                self._title_to_row[title] = self.navigation.count() - 1
        self.navigation.currentRowChanged.connect(self._emit_page_selected)
        self.navigation.currentRowChanged.connect(self._ensure_page_row)
        self.select_page("Dashboard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.addWidget(self.navigation)

    def _ensure_page_row(self, row: int) -> None:
        item = self.navigation.item(row)
        if item is not None and item.data(Qt.ItemDataRole.UserRole) == "section":
            self.select_page(self.page_titles[0])

    def _emit_page_selected(self, row: int) -> None:
        title = self.title_for_row(row)
        if title is not None:
            self.page_selected.emit(self._title_to_index[title])

    def select_page(self, title: str) -> None:
        row = self._title_to_row[title]
        self.navigation.setCurrentRow(row)

    def title_for_row(self, row: int) -> str | None:
        item = self.navigation.item(row)
        if item is None:
            return None
        title = item.data(Qt.ItemDataRole.UserRole)
        return title if title != "section" else None
