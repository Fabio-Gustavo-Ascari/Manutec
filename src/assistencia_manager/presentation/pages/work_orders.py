from __future__ import annotations

from PySide6.QtWidgets import (
    QComboBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from assistencia_manager.application.dto.work_order import OpenWorkOrderCommand, WorkOrderSearchQuery, WorkOrderStatusCommand
from assistencia_manager.application.services.work_order_service import WorkOrderService
from assistencia_manager.domain.entities.work_order import WorkOrderStatus
from assistencia_manager.domain.exceptions import DomainError
from assistencia_manager.domain.identifiers import EntityId


class WorkOrdersPage(QWidget):
    def __init__(self, service: WorkOrderService | None = None) -> None:
        super().__init__()
        self.service = service
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar defeito relatado")
        self.status_filter = QComboBox()
        self.status_filter.addItem("Todos", None)
        for status in WorkOrderStatus:
            self.status_filter.addItem(status.value, status)
        self.list_widget = QListWidget()
        self.client_input = QLineEdit()
        self.equipment_input = QLineEdit()
        self.issue_input = QLineEdit()
        open_button = QPushButton("Abrir ordem")
        refresh_button = QPushButton("Atualizar")
        approve_button = QPushButton("Aprovar")
        cancel_button = QPushButton("Cancelar")
        open_button.clicked.connect(self._open)
        refresh_button.clicked.connect(self.refresh)
        approve_button.clicked.connect(lambda: self._transition(WorkOrderStatus.APPROVED))
        cancel_button.clicked.connect(lambda: self._transition(WorkOrderStatus.CANCELLED))
        self.search_input.textChanged.connect(self.refresh)
        self.status_filter.currentIndexChanged.connect(self.refresh)
        form = QFormLayout()
        form.addRow("Cliente (UUID)", self.client_input)
        form.addRow("Equipamento (UUID)", self.equipment_input)
        form.addRow("Defeito relatado", self.issue_input)
        actions = QHBoxLayout()
        for button in (open_button, refresh_button, approve_button, cancel_button):
            actions.addWidget(button)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Ordens de serviço"))
        layout.addLayout(form)
        filters = QHBoxLayout(); filters.addWidget(self.search_input); filters.addWidget(self.status_filter)
        layout.addLayout(filters); layout.addLayout(actions); layout.addWidget(self.list_widget)

    def refresh(self) -> None:
        self.list_widget.clear()
        if self.service is None:
            return
        page = self.service.search(WorkOrderSearchQuery(self.search_input.text(), self.status_filter.currentData()))
        for order in page.items:
            self.list_widget.addItem(f"{order.id} — {order.status.value} — {order.reported_issue}")

    def _open(self) -> None:
        if self.service is None:
            return
        try:
            self.service.open(OpenWorkOrderCommand(EntityId.from_str(self.client_input.text()), EntityId.from_str(self.equipment_input.text()), self.issue_input.text()))
            self.refresh()
        except (DomainError, ValueError) as error:
            QMessageBox.warning(self, "Não foi possível abrir a ordem", str(error))

    def _transition(self, status: WorkOrderStatus) -> None:
        if self.service is None or self.list_widget.currentItem() is None:
            return
        try:
            identifier = EntityId.from_str(self.list_widget.currentItem().text().split(" — ", 1)[0])
            self.service.transition(WorkOrderStatusCommand(identifier, status))
            self.refresh()
        except (DomainError, ValueError) as error:
            QMessageBox.warning(self, "Não foi possível alterar a ordem", str(error))


# E10 keeps the historical import path stable while using the redesigned page.
from assistencia_manager.presentation.pages.e10_pages import WorkOrdersPage as WorkOrdersPage
