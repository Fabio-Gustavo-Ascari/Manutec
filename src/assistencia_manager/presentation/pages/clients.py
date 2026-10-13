from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
from assistencia_manager.application.dto.client import ClientSearchQuery, CreateClientCommand, UpdateClientCommand
from assistencia_manager.application.services.client_service import ClientService
from assistencia_manager.domain.exceptions import DomainValidationError
from assistencia_manager.domain.identifiers import EntityId


class ClientForm(QWidget):
    submitted = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent); self.identifier: EntityId | None = None
        self.name_input = QLineEdit(); self.name_input.setObjectName("clientNameInput")
        self.contacts_input = QLineEdit(); self.document_input = QLineEdit(); self.address_input = QLineEdit(); self.notes_input = QLineEdit()
        self.error_message = QLabel(); self.error_message.setObjectName("formError"); self.error_message.setStyleSheet("color: #b42318;")
        self.save_button = QPushButton("Salvar cliente"); self.save_button.clicked.connect(self.submit)
        fields = QFormLayout(); fields.addRow("Nome *", self.name_input); fields.addRow("Contatos", self.contacts_input); fields.addRow("Documento", self.document_input); fields.addRow("Endereço", self.address_input); fields.addRow("Observações", self.notes_input)
        layout = QVBoxLayout(self); layout.addLayout(fields); layout.addWidget(self.error_message); layout.addWidget(self.save_button)

    def set_client(self, client) -> None:
        self.identifier = client.id; self.name_input.setText(client.name); self.contacts_input.setText("; ".join(client.contacts)); self.document_input.setText(client.document or ""); self.address_input.setText(client.address or ""); self.notes_input.setText(client.notes or ""); self.save_button.setText("Atualizar cliente")

    def clear_form(self) -> None:
        self.identifier = None
        for field in (self.name_input, self.contacts_input, self.document_input, self.address_input, self.notes_input): field.clear()
        self.save_button.setText("Salvar cliente")

    def submit(self) -> None:
        self.error_message.clear(); name = self.name_input.text().strip()
        if not name: self.error_message.setText("Informe o nome do cliente."); return
        try:
            values = dict(name=name, contacts=tuple(v.strip() for v in self.contacts_input.text().split(";") if v.strip()), document=self.document_input.text() or None, address=self.address_input.text() or None, notes=self.notes_input.text() or None)
            command = UpdateClientCommand(identifier=self.identifier, **values) if self.identifier else CreateClientCommand(**values)
            if isinstance(self.parent(), ClientsPage): self.parent()._save_client(command)
            else: self.submitted.emit(command)
        except DomainValidationError as error: self.error_message.setText(str(error))


class ClientsPage(QWidget):
    def __init__(self, service: ClientService | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent); self.service = service; self._items = {}
        self.form = ClientForm(self); self.message = QLabel(); self.search_input = QLineEdit(); self.search_input.setPlaceholderText("Buscar cliente..."); self.page_input = QSpinBox(); self.page_input.setMinimum(1)
        search_button = QPushButton("Buscar"); search_button.clicked.connect(self.refresh); new_button = QPushButton("Novo"); new_button.clicked.connect(self.form.clear_form)
        self.results_table = QTableWidget(0, 4); self.results_table.setHorizontalHeaderLabels(["ID", "Nome", "Documento", "Status"]); self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        edit_button = QPushButton("Editar selecionado"); edit_button.clicked.connect(self.load_selected); deactivate_button = QPushButton("Inativar selecionado"); deactivate_button.clicked.connect(self.deactivate_selected)
        toolbar = QHBoxLayout(); toolbar.addWidget(self.search_input); toolbar.addWidget(self.page_input); toolbar.addWidget(search_button); toolbar.addWidget(new_button); actions = QHBoxLayout(); actions.addWidget(edit_button); actions.addWidget(deactivate_button)
        layout = QVBoxLayout(self); layout.addWidget(QLabel("Clientes")); layout.addLayout(toolbar); layout.addWidget(self.results_table); layout.addLayout(actions); layout.addWidget(self.form); layout.addWidget(self.message)

    def refresh(self) -> None:
        if self.service is None: return
        result = self.service.search(ClientSearchQuery(search=self.search_input.text().strip() or None, page=self.page_input.value())); self._items = {str(item.id): item for item in result.items}; self.results_table.setRowCount(0)
        for item in result.items:
            row = self.results_table.rowCount(); self.results_table.insertRow(row)
            for column, value in enumerate((str(item.id), item.name, item.document or "", item.status.value)): self.results_table.setItem(row, column, QTableWidgetItem(value))
        self.message.setText(f"{result.total_items} cliente(s) encontrado(s).")

    def _selected(self):
        row = self.results_table.currentRow()
        if row < 0 or self.results_table.item(row, 0) is None: return None
        return self._items.get(self.results_table.item(row, 0).text())

    def load_selected(self) -> None:
        item = self._selected()
        if item: self.form.set_client(item); self.message.setText("Cliente carregado para edição.")

    def _save_client(self, command) -> None:
        if self.service is None: return
        try:
            self.service.update(command) if isinstance(command, UpdateClientCommand) else self.service.create(command); self.form.clear_form(); self.message.setText("Cliente atualizado com sucesso." if isinstance(command, UpdateClientCommand) else "Cliente salvo com sucesso."); self.refresh()
        except Exception as error: self.form.error_message.setText(str(error))

    def deactivate_selected(self) -> None:
        item = self._selected()
        if item is None or self.service is None: return
        if QMessageBox.question(self, "Inativar cliente", "Deseja inativar o cliente selecionado?") == QMessageBox.StandardButton.Yes:
            try: self.service.deactivate(item.id); self.refresh(); self.message.setText("Cliente inativado com sucesso.")
            except Exception as error: self.form.error_message.setText(str(error))
