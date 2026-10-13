from pathlib import Path
from PySide6.QtWidgets import QComboBox, QFileDialog, QLabel, QPushButton, QVBoxLayout, QWidget

class ReportsPage(QWidget):
    def __init__(self, report_service=None):
        super().__init__(); self.report_service = report_service
        self.kind = QComboBox(); self.kind.addItems(("work_orders", "sales", "inventory", "purchases", "finance", "margin", "productivity", "warranties"))
        self.status = QComboBox(); self.status.addItem("Todos", "")
        self.status.addItems(("open", "completed", "delivered", "cancelled", "paid", "pending"))
        self.message = QLabel("Selecione um relatório para exportar.")
        csv_button = QPushButton("Exportar CSV"); pdf_button = QPushButton("Exportar PDF")
        csv_button.clicked.connect(lambda: self.export("csv")); pdf_button.clicked.connect(lambda: self.export("pdf"))
        layout = QVBoxLayout(self); layout.addWidget(QLabel("Relatórios gerenciais")); layout.addWidget(self.kind); layout.addWidget(self.status); layout.addWidget(csv_button); layout.addWidget(pdf_button); layout.addWidget(self.message); layout.addStretch()
    def export(self, extension):
        if self.report_service is None: return
        destination, _ = QFileDialog.getSaveFileName(self, "Exportar relatório", f"relatorio.{extension}", f"{extension.upper()} (*.{extension})")
        if not destination: return
        result = self.report_service.generate(self.kind.currentData() or self.kind.currentText())
        path = (self.report_service.export_csv(result, Path(destination)) if extension == "csv" else self.report_service.export_pdf(result, Path(destination)))
        self.message.setText(f"Exportado: {path.name}")
