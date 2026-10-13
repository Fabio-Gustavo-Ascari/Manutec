from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QFormLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from assistencia_manager.application.dto.fiscal import FiscalConfigurationCommand
from assistencia_manager.domain.entities.fiscal import FiscalEnvironment


class FiscalPage(QWidget):
    def __init__(self, service=None) -> None:
        super().__init__()
        self.service = service
        self.document = QLineEdit()
        self.provider = QLineEdit("simulated")
        self.environment = QComboBox()
        self.environment.addItems(["homologation", "production"])
        form = QFormLayout()
        form.addRow("CNPJ/CPF da empresa", self.document)
        form.addRow("Provedor", self.provider)
        form.addRow("Ambiente", self.environment)
        save = QPushButton("Salvar configuração fiscal")
        save.clicked.connect(self.save)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Fiscal e periféricos"))
        layout.addLayout(form)
        layout.addWidget(save)
        layout.addWidget(QLabel("NF-e, NFC-e, NFS-e, impressora térmica/A4, leitor e PIX usam adaptadores configuráveis."))
        layout.addStretch()
        self.load()

    def load(self) -> None:
        if self.service and (configuration := self.service.get_configuration()):
            self.document.setText(configuration.company_document)
            self.provider.setText(configuration.provider)
            self.environment.setCurrentText(configuration.environment.value)

    def save(self) -> None:
        if self.service:
            self.service.configure(FiscalConfigurationCommand(
                company_document=self.document.text(), provider=self.provider.text(),
                environment=FiscalEnvironment(self.environment.currentText()),
            ))
