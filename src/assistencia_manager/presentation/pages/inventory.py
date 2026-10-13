from __future__ import annotations

from decimal import Decimal

from PySide6.QtWidgets import (
    QFormLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget, QMessageBox,
    QPushButton, QVBoxLayout, QWidget,
)

from assistencia_manager.application.dto.inventory import (
    CreatePartCommand, PartSearchQuery, RecordInventoryMovementCommand,
)
from assistencia_manager.application.services.inventory_service import InventoryService
from assistencia_manager.domain.entities.inventory import InventoryMovementType
from assistencia_manager.domain.exceptions import DomainError
from assistencia_manager.domain.identifiers import EntityId


class InventoryPage(QWidget):
    def __init__(self, service: InventoryService | None = None) -> None:
        super().__init__()
        self.service = service
        self.name_input = QLineEdit()
        self.category_input = QLineEdit()
        self.unit_input = QLineEdit("un")
        self.sku_input = QLineEdit()
        self.cost_input = QLineEdit("0")
        self.price_input = QLineEdit("0")
        self.minimum_stock_input = QLineEdit("0")
        self.quantity_input = QLineEdit()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar peça")
        self.list_widget = QListWidget()
        create_button = QPushButton("Cadastrar peça")
        entry_button = QPushButton("Entrada")
        exit_button = QPushButton("Saída")
        refresh_button = QPushButton("Atualizar")
        create_button.clicked.connect(self._create)
        entry_button.clicked.connect(lambda: self._movement(InventoryMovementType.ENTRY))
        exit_button.clicked.connect(lambda: self._movement(InventoryMovementType.EXIT))
        refresh_button.clicked.connect(self.refresh)
        self.search_input.textChanged.connect(self.refresh)
        form = QFormLayout()
        form.addRow("Nome", self.name_input)
        form.addRow("Categoria", self.category_input)
        form.addRow("Unidade", self.unit_input)
        form.addRow("SKU", self.sku_input)
        form.addRow("Custo", self.cost_input)
        form.addRow("Preço", self.price_input)
        form.addRow("Estoque mínimo", self.minimum_stock_input)
        form.addRow("Quantidade", self.quantity_input)
        actions = QHBoxLayout()
        for button in (create_button, entry_button, exit_button, refresh_button):
            actions.addWidget(button)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Estoque e peças"))
        layout.addLayout(form)
        layout.addWidget(self.search_input)
        layout.addLayout(actions)
        layout.addWidget(self.list_widget)

    def refresh(self) -> None:
        self.list_widget.clear()
        if self.service is None:
            return
        page = self.service.search(PartSearchQuery(self.search_input.text()))
        for part in page.items:
            physical, available = self.service.balance(part.id)
            alert = " — estoque mínimo" if physical <= part.minimum_stock else ""
            self.list_widget.addItem(f"{part.id} — {part.name} — saldo {physical} — disponível {available}{alert}")

    def _create(self) -> None:
        if self.service is None:
            return
        try:
            self.service.create_part(CreatePartCommand(
                name=self.name_input.text(), category=self.category_input.text(),
                unit=self.unit_input.text(), sku=self.sku_input.text() or None,
                cost=Decimal(self.cost_input.text() or "0"),
                price=Decimal(self.price_input.text() or "0"),
                minimum_stock=Decimal(self.minimum_stock_input.text() or "0"),
            ))
            self.refresh()
        except (DomainError, ValueError) as error:
            QMessageBox.warning(self, "Não foi possível cadastrar a peça", str(error))

    def _movement(self, movement_type: InventoryMovementType) -> None:
        if self.service is None or self.list_widget.currentItem() is None:
            return
        try:
            identifier = EntityId.from_str(self.list_widget.currentItem().text().split(" — ", 1)[0])
            self.service.record_movement(RecordInventoryMovementCommand(
                identifier, movement_type, Decimal(self.quantity_input.text()),
            ))
            self.refresh()
        except (DomainError, ValueError) as error:
            QMessageBox.warning(self, "Não foi possível movimentar o estoque", str(error))


from assistencia_manager.presentation.pages.e21_pages import InventoryPage as InventoryPage
