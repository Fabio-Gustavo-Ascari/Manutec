from PySide6.QtWidgets import QLabel, QListWidget, QVBoxLayout, QWidget

from assistencia_manager.application.services.procurement_service import ProcurementService


class PurchasesPage(QWidget):
    """Consulta operacional dos pedidos; criação/recebimento usam o serviço transacional."""

    def __init__(self, service: ProcurementService | None = None) -> None:
        super().__init__()
        self.service = service
        self.list_widget = QListWidget()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Compras e recebimentos"))
        layout.addWidget(self.list_widget)

    def refresh(self) -> None:
        self.list_widget.clear()
        if self.service is None:
            return
        # The service remains the only boundary to persistence; the list is optional
        # in installations that use the dedicated purchasing workflow.
        for suggestion in self.service.reorder_suggestions():
            self.list_widget.addItem(f"Reposição: {suggestion.part_id} — sugerido {suggestion.suggested_quantity}")
