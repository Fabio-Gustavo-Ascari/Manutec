from __future__ import annotations

from PySide6.QtWidgets import QFormLayout, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget

from assistencia_manager.application.services.company_settings_service import CompanySettingsService
from assistencia_manager.domain.exceptions import DomainError


class CompanySettingsPage(QWidget):
    def __init__(self, service: CompanySettingsService | None = None) -> None:
        super().__init__()
        self.service = service
        self.inputs = {field: QLineEdit() for field in CompanySettingsService.FIELDS}
        form = QFormLayout()
        labels = {"name": "Nome", "document": "Documento", "address": "Endereço", "phone": "Telefone", "email": "E-mail"}
        for field, input_widget in self.inputs.items():
            form.addRow(labels[field], input_widget)
        save = QPushButton("Salvar configurações")
        save.clicked.connect(self.save)
        layout = QVBoxLayout(self)
        layout.addWidget(QPushButton("Configurações da empresa"))
        layout.addLayout(form)
        layout.addWidget(save)
        layout.addStretch()
        self.load()

    def load(self) -> None:
        if self.service:
            for field, value in self.service.get().items():
                self.inputs[field].setText(value)

    def save(self) -> None:
        if not self.service:
            return
        try:
            self.service.update({field: input_widget.text() for field, input_widget in self.inputs.items()})
            QMessageBox.information(self, "Configurações", "Configurações salvas")
        except DomainError as error:
            QMessageBox.warning(self, "Configurações", str(error))
