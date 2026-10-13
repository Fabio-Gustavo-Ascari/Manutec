from __future__ import annotations

from decimal import Decimal
from PySide6.QtWidgets import QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTabWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from assistencia_manager.application.dto.catalog import CreateCatalogCommand, CreateServiceCommand, CreateWarrantyRuleCommand
from assistencia_manager.domain.entities.catalog import CatalogType


class CatalogsPage(QWidget):
    def __init__(self, service=None):
        super().__init__(); self.service = service
        self.kind = CatalogType.CATEGORY; self.name = QLineEdit(); self.price = QLineEdit("0"); self.days = QLineEdit("0"); self.applies = QLineEdit("serviço")
        self.search = QLineEdit(); self.search.setPlaceholderText("Buscar cadastro"); self.table = QTableWidget(0, 3); self.table.setHorizontalHeaderLabels(("Tipo", "Nome", "Detalhes"))
        self.type_input = QLineEdit("categoria")
        save = QPushButton("Cadastrar"); save.setObjectName("primaryAction"); save.clicked.connect(self._save); refresh = QPushButton("Atualizar"); refresh.clicked.connect(self.refresh); self.search.textChanged.connect(self.refresh)
        form = QFormLayout(); form.addRow("Tipo (categoria/marca/fornecedor/técnico)", self.type_input); form.addRow("Nome", self.name); form.addRow("Preço do serviço", self.price); form.addRow("Dias de garantia", self.days); form.addRow("Aplicação", self.applies)
        actions = QHBoxLayout(); actions.addWidget(save); actions.addWidget(refresh)
        tabs = QTabWidget(); tabs.addTab(QLabel("Cadastre categorias, marcas, fornecedores e técnicos pelo formulário abaixo."), "Cadastros auxiliares"); tabs.addTab(QLabel("Serviços e pacotes podem ser consultados e usados na OS."), "Serviços")
        layout = QVBoxLayout(self); layout.addWidget(tabs); layout.addLayout(form); layout.addLayout(actions); layout.addWidget(self.search); layout.addWidget(self.table)
        self.refresh()

    def _kind(self):
        return {"categoria": CatalogType.CATEGORY, "marca": CatalogType.BRAND, "fornecedor": CatalogType.SUPPLIER, "técnico": CatalogType.TECHNICIAN, "tecnico": CatalogType.TECHNICIAN}.get(self.type_input.text().strip().casefold(), CatalogType.CATEGORY)

    def _save(self):
        if not self.service: return
        if self.type_input.text().strip().casefold() == "serviço":
            self.service.create_service(CreateServiceCommand(self.name.text(), Decimal(self.price.text()), int(self.days.text()), None))
            self.refresh(); return
        kind = self._kind()
        self.service.create_catalog(CreateCatalogCommand(kind, self.name.text()))
        self.refresh()

    def refresh(self):
        self.table.setRowCount(0)
        if not self.service: return
        for item in self.service.search_catalogs(self._kind(), self.search.text() or None):
            row = self.table.rowCount(); self.table.insertRow(row); self.table.setItem(row, 0, QTableWidgetItem(item.kind.value)); self.table.setItem(row, 1, QTableWidgetItem(item.name)); self.table.setItem(row, 2, QTableWidgetItem(item.phone or item.email or ""))
