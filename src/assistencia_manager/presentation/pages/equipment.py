from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
from assistencia_manager.application.dto.equipment import EquipmentSearchQuery, CreateEquipmentCommand, UpdateEquipmentCommand
from assistencia_manager.application.services.equipment_service import EquipmentService
from assistencia_manager.domain.exceptions import DomainValidationError
from assistencia_manager.domain.identifiers import EntityId


class EquipmentForm(QWidget):
    submitted = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent); self.identifier = None
        self.client_id_input = QLineEdit(); self.client_id_input.setPlaceholderText("UUID do cliente"); self.equipment_type_input = QLineEdit(); self.brand_input = QLineEdit(); self.model_input = QLineEdit(); self.serial_number_input = QLineEdit(); self.accessories_input = QLineEdit()
        self.error_message = QLabel(); self.error_message.setObjectName("formError"); self.error_message.setStyleSheet("color: #b42318;"); self.save_button = QPushButton("Salvar equipamento"); self.save_button.clicked.connect(self.submit)
        fields = QFormLayout(); fields.addRow("Cliente *", self.client_id_input); fields.addRow("Tipo *", self.equipment_type_input); fields.addRow("Marca", self.brand_input); fields.addRow("Modelo", self.model_input); fields.addRow("Número de série", self.serial_number_input); fields.addRow("Acessórios", self.accessories_input)
        layout = QVBoxLayout(self); layout.addLayout(fields); layout.addWidget(self.error_message); layout.addWidget(self.save_button)

    def set_equipment(self, equipment) -> None:
        self.identifier = equipment.id; self.client_id_input.setText(str(equipment.client_id)); self.equipment_type_input.setText(equipment.equipment_type); self.brand_input.setText(equipment.brand or ""); self.model_input.setText(equipment.model or ""); self.serial_number_input.setText(equipment.serial_number or ""); self.accessories_input.setText("; ".join(equipment.accessories)); self.client_id_input.setEnabled(False); self.save_button.setText("Atualizar equipamento")

    def clear_form(self) -> None:
        self.identifier = None; self.client_id_input.setEnabled(True)
        for field in (self.client_id_input, self.equipment_type_input, self.brand_input, self.model_input, self.serial_number_input, self.accessories_input): field.clear()
        self.save_button.setText("Salvar equipamento")

    def submit(self) -> None:
        self.error_message.clear()
        if not self.client_id_input.text().strip() or not self.equipment_type_input.text().strip(): self.error_message.setText("Informe o cliente e o tipo do equipamento."); return
        try:
            values = dict(equipment_type=self.equipment_type_input.text(), brand=self.brand_input.text() or None, model=self.model_input.text() or None, serial_number=self.serial_number_input.text() or None, accessories=tuple(v.strip() for v in self.accessories_input.text().split(";") if v.strip()))
            command = UpdateEquipmentCommand(identifier=self.identifier, **values) if self.identifier else CreateEquipmentCommand(client_id=EntityId.from_str(self.client_id_input.text().strip()), **values)
            if isinstance(self.parent(), EquipmentPage): self.parent()._save_equipment(command)
            else: self.submitted.emit(command)
        except (DomainValidationError, ValueError): self.error_message.setText("Informe um identificador de cliente válido.")


class EquipmentPage(QWidget):
    def __init__(self, service: EquipmentService | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent); self.service = service; self._items = {}
        self.form = EquipmentForm(self); self.message = QLabel(); self.search_input = QLineEdit(); self.search_input.setPlaceholderText("Buscar equipamento..."); self.page_input = QSpinBox(); self.page_input.setMinimum(1)
        search_button = QPushButton("Buscar"); search_button.clicked.connect(self.refresh); new_button = QPushButton("Novo"); new_button.clicked.connect(self.form.clear_form)
        self.results_table = QTableWidget(0, 5); self.results_table.setHorizontalHeaderLabels(["ID", "Tipo", "Marca", "Modelo", "Status"]); self.results_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        edit_button = QPushButton("Editar selecionado"); edit_button.clicked.connect(self.load_selected); deactivate_button = QPushButton("Inativar selecionado"); deactivate_button.clicked.connect(self.deactivate_selected)
        toolbar = QHBoxLayout(); toolbar.addWidget(self.search_input); toolbar.addWidget(self.page_input); toolbar.addWidget(search_button); toolbar.addWidget(new_button); actions = QHBoxLayout(); actions.addWidget(edit_button); actions.addWidget(deactivate_button)
        layout = QVBoxLayout(self); layout.addWidget(QLabel("Equipamentos")); layout.addLayout(toolbar); layout.addWidget(self.results_table); layout.addLayout(actions); layout.addWidget(self.form); layout.addWidget(self.message)

    def refresh(self) -> None:
        if self.service is None: return
        result = self.service.search(EquipmentSearchQuery(search=self.search_input.text().strip() or None, page=self.page_input.value())); self._items = {str(item.id): item for item in result.items}; self.results_table.setRowCount(0)
        for item in result.items:
            row = self.results_table.rowCount(); self.results_table.insertRow(row)
            for column, value in enumerate((str(item.id), item.equipment_type, item.brand or "", item.model or "", item.status.value)): self.results_table.setItem(row, column, QTableWidgetItem(value))
        self.message.setText(f"{result.total_items} equipamento(s) encontrado(s).")

    def _selected(self):
        row = self.results_table.currentRow()
        if row < 0 or self.results_table.item(row, 0) is None: return None
        return self._items.get(self.results_table.item(row, 0).text())

    def load_selected(self) -> None:
        item = self._selected()
        if item: self.form.set_equipment(item); self.message.setText("Equipamento carregado para edição.")

    def _save_equipment(self, command) -> None:
        if self.service is None: return
        try:
            self.service.update(command) if isinstance(command, UpdateEquipmentCommand) else self.service.create(command); self.form.clear_form(); self.message.setText("Equipamento atualizado com sucesso." if isinstance(command, UpdateEquipmentCommand) else "Equipamento salvo com sucesso."); self.refresh()
        except Exception as error: self.form.error_message.setText(str(error))

    def deactivate_selected(self) -> None:
        item = self._selected()
        if item is None or self.service is None: return
        if QMessageBox.question(self, "Inativar equipamento", "Deseja inativar o equipamento selecionado?") == QMessageBox.StandardButton.Yes:
            try: self.service.deactivate(item.id); self.refresh(); self.message.setText("Equipamento inativado com sucesso.")
            except Exception as error: self.form.error_message.setText(str(error))
