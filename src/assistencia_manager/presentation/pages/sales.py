from __future__ import annotations

from decimal import Decimal
from PySide6.QtWidgets import QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget

from assistencia_manager.application.dto.sales import AddSaleItemCommand, CreateSaleCommand, RecordPaymentCommand
from assistencia_manager.application.services.sales_service import SalesService
from assistencia_manager.domain.entities.sales import PaymentMethod
from assistencia_manager.domain.exceptions import DomainError


class SalesPage(QWidget):
    def __init__(self, service: SalesService | None = None) -> None:
        super().__init__()
        self.service = service
        self.sale = None
        self.description_input, self.quantity_input, self.price_input, self.payment_input = (QLineEdit() for _ in range(4))
        self.quantity_input.setText("1")
        self.payment_input.setText("0")
        create, add, complete, pay = (QPushButton(label) for label in ("Nova venda", "Adicionar item", "Concluir", "Receber PIX"))
        create.clicked.connect(self._create)
        add.clicked.connect(self._add)
        complete.clicked.connect(self._complete)
        pay.clicked.connect(self._pay)
        self.status = QLabel("Nenhuma venda aberta")
        form = QFormLayout()
        form.addRow("Descrição", self.description_input)
        form.addRow("Quantidade", self.quantity_input)
        form.addRow("Preço unitário", self.price_input)
        form.addRow("Valor recebido", self.payment_input)
        actions = QHBoxLayout()
        for button in (create, add, complete, pay): actions.addWidget(button)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Vendas e pagamentos"))
        layout.addLayout(form)
        layout.addLayout(actions)
        layout.addWidget(self.status)

    def _create(self) -> None:
        if self.service is None: return
        try:
            self.sale = self.service.create(CreateSaleCommand())
            self.status.setText(f"Venda aberta: {self.sale.id}")
        except (DomainError, ValueError) as error: QMessageBox.warning(self, "Não foi possível abrir a venda", str(error))

    def _add(self) -> None:
        if self.service is None or self.sale is None: return
        try:
            self.sale = self.service.add_item(AddSaleItemCommand(self.sale.id, self.description_input.text(), Decimal(self.quantity_input.text()), Decimal(self.price_input.text())))
            self.status.setText(f"Venda {self.sale.id} — total {self.sale.total}")
        except (DomainError, ValueError) as error: QMessageBox.warning(self, "Não foi possível adicionar o item", str(error))

    def _complete(self) -> None:
        if self.service is None or self.sale is None: return
        try: self.sale = self.service.complete(self.sale.id); self.status.setText(f"Venda concluída — total {self.sale.total}")
        except (DomainError, ValueError) as error: QMessageBox.warning(self, "Não foi possível concluir a venda", str(error))

    def _pay(self) -> None:
        if self.service is None or self.sale is None: return
        try:
            payment = self.service.record_payment(RecordPaymentCommand(self.sale.id, Decimal(self.payment_input.text()), PaymentMethod.PIX))
            self.status.setText(f"Recebido {payment.amount} — pagamento {payment.id}")
        except (DomainError, ValueError) as error: QMessageBox.warning(self, "Não foi possível registrar o pagamento", str(error))


from assistencia_manager.presentation.pages.e21_pages import SalesPage as SalesPage
