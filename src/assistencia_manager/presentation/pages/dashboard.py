from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QFormLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from assistencia_manager.application.services.dashboard_service import DashboardService
from assistencia_manager.application.services.report_service import ReportService


class DashboardPage(QWidget):
    def __init__(self, dashboard_service: DashboardService | None = None, report_service: ReportService | None = None) -> None:
        super().__init__()
        self.dashboard_service = dashboard_service
        self.report_service = report_service
        self.orders_label = QLabel()
        self.overdue_label = QLabel()
        self.revenue_label = QLabel()
        self.stock_label = QLabel()
        refresh = QPushButton("Atualizar indicadores")
        export = QPushButton("Exportar relatório de ordens")
        refresh.clicked.connect(self.refresh)
        export.clicked.connect(self.export_orders)
        form = QFormLayout()
        form.addRow("Ordens por status", self.orders_label)
        form.addRow("Ordens atrasadas", self.overdue_label)
        form.addRow("Receita recebida", self.revenue_label)
        form.addRow("Peças no estoque mínimo", self.stock_label)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Dashboard operacional"))
        layout.addLayout(form)
        layout.addWidget(refresh)
        layout.addWidget(export)
        layout.addStretch()
        self.refresh()

    def refresh(self) -> None:
        if self.dashboard_service is None:
            self.orders_label.setText("Serviço não configurado")
            self.overdue_label.setText("-")
            self.revenue_label.setText("-")
            self.stock_label.setText("-")
            return
        snapshot = self.dashboard_service.snapshot()
        self.orders_label.setText(", ".join(f"{key}: {value}" for key, value in sorted(snapshot.orders_by_status.items())) or "Nenhuma")
        self.overdue_label.setText(str(snapshot.overdue_orders))
        self.revenue_label.setText(f"R$ {snapshot.received_revenue:.2f}")
        self.stock_label.setText(str(snapshot.low_stock_parts))

    def export_orders(self) -> None:
        if self.report_service is None:
            return
        destination, _ = QFileDialog.getSaveFileName(self, "Exportar relatório", "ordens.csv", "CSV (*.csv)")
        if destination:
            self.report_service.export_orders_csv(self.report_service.orders(), Path(destination))
