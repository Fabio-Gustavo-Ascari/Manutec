from __future__ import annotations

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import QListWidget, QListWidgetItem, QVBoxLayout, QWidget

from assistencia_manager.presentation.navigation.icons import navigation_icon


class Sidebar(QWidget):
    page_selected = Signal(int)

    def __init__(self, page_definitions: tuple[tuple[str, str], ...]) -> None:
        super().__init__()
        self.setObjectName("sidebar")
        self.setMinimumWidth(196)
        self.setMaximumWidth(240)
        self.section_labels = ["Operação", "Base e compras", "Financeiro e fiscal", "Administração"]
        groups = {
            "Operação": {"Dashboard", "Ordens de serviço", "Estoque", "Vendas"},
            "Base e compras": {"Clientes", "Equipamentos", "Cadastros", "Compras"},
            "Financeiro e fiscal": {"Financeiro", "Fiscal e periféricos"},
            "Administração": {"Configurações", "Relatórios", "Usuários e auditoria"},
        }
        self.navigation = QListWidget()
        self.navigation.setObjectName("navigation")
        self.navigation.setIconSize(QSize(20, 20))
        self.navigation.setSpacing(3)
        self._section_items: dict[str, list[QListWidgetItem]] = {}
        self.page_titles: list[str] = []
        self._title_to_row: dict[str, int] = {}
        self._title_to_index = {title: index for index, (title, _description) in enumerate(page_definitions)}
        for section in self.section_labels:
            heading = QListWidgetItem(section)
            heading.setData(Qt.ItemDataRole.UserRole, "section")
            heading.setFlags(Qt.ItemFlag.ItemIsEnabled)
            heading.setIcon(navigation_icon("expanded"))
            heading.setForeground(QColor("#667085"))
            font = QFont()
            font.setPointSize(9)
            font.setBold(True)
            heading.setFont(font)
            heading.setToolTip("Clique para recolher ou expandir este grupo")
            self._section_items[section] = []
            self.navigation.addItem(heading)
            for title, _description in page_definitions:
                if title not in groups[section]:
                    continue
                item = QListWidgetItem(title)
                item.setIcon(navigation_icon(title))
                item.setSizeHint(QSize(180, 42))
                item.setData(Qt.ItemDataRole.UserRole, title)
                self.navigation.addItem(item)
                self._section_items[section].append(item)
                self.page_titles.append(title)
                self._title_to_row[title] = self.navigation.count() - 1
        self.navigation.currentRowChanged.connect(self._emit_page_selected)
        self.navigation.itemClicked.connect(self._toggle_section)
        self.navigation.itemActivated.connect(self._toggle_section)
        self.select_page("Dashboard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.addWidget(self.navigation)

    def _toggle_section(self, item: QListWidgetItem) -> None:
        if item.data(Qt.ItemDataRole.UserRole) != "section":
            return
        children = self._section_items[item.text()]
        if not children:
            return
        hide = not children[0].isHidden()
        for child in children:
            child.setHidden(hide)
        item.setIcon(navigation_icon("collapsed" if hide else "expanded"))

    def _emit_page_selected(self, row: int) -> None:
        title = self.title_for_row(row)
        if title is not None:
            self.page_selected.emit(self._title_to_index[title])

    def select_page(self, title: str) -> None:
        row = self._title_to_row[title]
        for section, children in self._section_items.items():
            if self.navigation.item(row) in children and self.navigation.item(row).isHidden():
                for child in children:
                    child.setHidden(False)
                for index in range(self.navigation.count()):
                    heading = self.navigation.item(index)
                    if heading.text() == section:
                        heading.setIcon(navigation_icon("expanded"))
        self.navigation.setCurrentRow(row)

    def title_for_row(self, row: int) -> str | None:
        item = self.navigation.item(row)
        if item is None:
            return None
        title = item.data(Qt.ItemDataRole.UserRole)
        return title if title != "section" else None
