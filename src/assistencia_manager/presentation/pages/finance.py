from PySide6.QtWidgets import QLabel, QListWidget, QVBoxLayout, QWidget


class FinancePage(QWidget):
    def __init__(self, service=None) -> None:
        super().__init__()
        self.service = service
        self.list_widget = QListWidget()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Financeiro — contas a pagar e receber"))
        layout.addWidget(self.list_widget)
        self.refresh()

    def refresh(self) -> None:
        self.list_widget.clear()
        if self.service is None:
            return
        with self.service._unit_of_work_factory() as uow:
            for entry in uow.financial_entries.list():
                self.list_widget.addItem(f"{entry.entry_type.value}: {entry.description} — R$ {entry.amount} — {entry.status.value}")
