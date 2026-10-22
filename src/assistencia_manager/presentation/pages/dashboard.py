from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import QFileDialog, QGridLayout, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from assistencia_manager.application.services.dashboard_service import DashboardService
from assistencia_manager.application.services.report_service import ReportService
from assistencia_manager.presentation.shell import DashboardMetricCard, PageShell
from assistencia_manager.presentation.navigation.icons import navigation_icon


PRIMARY_MODULES = (
    ("Financeiro", "Contas e fluxo de caixa"),
    ("Estoque", "Peças, saldos e movimentações"),
    ("Ordens de serviço", "Abertura e acompanhamento"),
    ("Vendas", "Vendas, recebimentos e caixa"),
    ("Clientes", "Cadastro e atendimento"),
    ("Compras", "Pedidos e reposição"),
)
OTHER_MODULES = (
    ("Equipamentos", "Aparelhos dos clientes"),
    ("Cadastros", "Produtos, serviços e parceiros"),
    ("Fiscal e periféricos", "Documentos e dispositivos"),
    ("Relatórios", "Análises e exportações"),
    ("Configurações", "Dados da assistência"),
    ("Usuários e auditoria", "Acessos e histórico"),
)


class DashboardPage(QWidget):
    navigation_requested = Signal(str)

    def __init__(self, dashboard_service: DashboardService | None = None, report_service: ReportService | None = None) -> None:
        super().__init__()
        self.dashboard_service = dashboard_service
        self.report_service = report_service
        refresh = QPushButton("Atualizar")
        refresh.clicked.connect(self.refresh)
        self.page_shell = PageShell("Início", "Tudo o que você precisa para cuidar da sua assistência.", actions=[refresh])
        self.module_buttons: dict[str, QPushButton] = {}
        self.page_shell.body.addLayout(self._module_grid(PRIMARY_MODULES))
        self.metric_cards = {
            "orders": DashboardMetricCard("Ordens em andamento", accent="primary"),
            "overdue": DashboardMetricCard("Ordens atrasadas", accent="danger"),
            "revenue": DashboardMetricCard("Receita recebida", accent="success"),
            "stock": DashboardMetricCard("Peças no estoque mínimo", accent="warning"),
        }
        self.orders_label = self.metric_cards["orders"].value_label
        self.overdue_label = self.metric_cards["overdue"].value_label
        self.revenue_label = self.metric_cards["revenue"].value_label
        self.stock_label = self.metric_cards["stock"].value_label
        metrics = QGridLayout()
        metrics.setHorizontalSpacing(12)
        metrics.setVerticalSpacing(12)
        for index, card in enumerate(self.metric_cards.values()):
            metrics.addWidget(card, index // 2, index % 2)
        metrics.setColumnStretch(0, 1)
        metrics.setColumnStretch(1, 1)
        self.quick_actions = QHBoxLayout()
        for text, slot, primary in (
            ("Nova ordem de serviço", self._quick_order, True),
            ("Registrar venda", self._quick_sale, False),
            ("Repor estoque", self._quick_stock, False),
        ):
            button = QPushButton(text)
            if primary:
                button.setObjectName("primaryAction")
            button.clicked.connect(slot)
            self.quick_actions.addWidget(button)
        self.status_summary = QLabel()
        self.status_summary.setObjectName("pageSubtitle")
        export = QPushButton("Exportar relatório de ordens")
        export.clicked.connect(self.export_orders)
        layout = QVBoxLayout()
        overview = QLabel("Resumo da operação")
        overview.setObjectName("sectionTitle")
        layout.addWidget(overview)
        layout.addLayout(metrics)
        layout.addWidget(QLabel("Ações rápidas"), alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addLayout(self.quick_actions)
        layout.addWidget(QLabel("Distribuição por status"), alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.status_summary)
        layout.addWidget(export, alignment=Qt.AlignmentFlag.AlignLeft)
        other_heading = QLabel("Mais módulos")
        other_heading.setObjectName("sectionTitle")
        layout.addWidget(other_heading)
        layout.addLayout(self._module_grid(OTHER_MODULES, compact=True))
        layout.addStretch()
        self.page_shell.body.addLayout(layout)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 18, 18, 18)
        outer.addWidget(self.page_shell)
        self.refresh()

    def _module_grid(self, modules, *, compact: bool = False) -> QGridLayout:
        grid = QGridLayout()
        grid.setSpacing(12)
        for index, (title, description) in enumerate(modules):
            button = QPushButton()
            button.setObjectName("moduleShortcut")
            button.setProperty("compact", compact)
            button.setAccessibleName(title)
            button.setToolTip(f"Abrir {title}")
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setMinimumHeight(66 if compact else 86)
            button.clicked.connect(lambda checked=False, target=title: self.navigation_requested.emit(target))
            row = QHBoxLayout(button)
            row.setContentsMargins(16, 12, 12, 12)
            row.setSpacing(12)
            icon = QLabel()
            icon.setPixmap(navigation_icon(title).pixmap(QSize(26, 26)))
            row.addWidget(icon)
            text = QVBoxLayout()
            text.setSpacing(4)
            label = QLabel(title)
            label.setObjectName("moduleTitle")
            label.setWordWrap(True)
            text.addWidget(label)
            if not compact:
                detail = QLabel(description)
                detail.setObjectName("moduleDescription")
                detail.setWordWrap(True)
                text.addWidget(detail)
            row.addLayout(text, 1)
            arrow = QLabel("›")
            arrow.setObjectName("moduleArrow")
            row.addWidget(arrow)
            # Labels must never intercept clicks intended for the whole tile.
            for child in button.findChildren(QWidget):
                child.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            self.module_buttons[title] = button
            grid.addWidget(button, index // 3, index % 3)
        for column in range(3):
            grid.setColumnStretch(column, 1)
        return grid

    def refresh(self) -> None:
        if self.dashboard_service is None:
            for card in self.metric_cards.values():
                card.set_value("—", "Serviço não configurado")
            self.status_summary.setText("Configure o serviço para carregar os indicadores.")
            return
        snapshot = self.dashboard_service.snapshot()
        total_orders = sum(snapshot.orders_by_status.values())
        self.metric_cards["orders"].set_value(str(total_orders), "total no fluxo")
        self.metric_cards["overdue"].set_value(str(snapshot.overdue_orders), "exigem atenção")
        self.metric_cards["revenue"].set_value(f"R$ {snapshot.received_revenue:.2f}", "recebido")
        self.metric_cards["stock"].set_value(str(snapshot.low_stock_parts), "itens para reposição")
        self.status_summary.setText(", ".join(f"{key}: {value}" for key, value in sorted(snapshot.orders_by_status.items())) or "Nenhuma ordem registrada")

    def _quick_order(self) -> None:
        self.navigation_requested.emit("Ordens de serviço")
        self.statusBarMessage("Abertura de ordem disponível na tela de Ordens de serviço.")

    def _quick_sale(self) -> None:
        self.navigation_requested.emit("Vendas")
        self.statusBarMessage("Registro de venda disponível na tela de Vendas.")

    def _quick_stock(self) -> None:
        self.navigation_requested.emit("Estoque")
        self.statusBarMessage("Reposição disponível na tela de Estoque.")

    def statusBarMessage(self, message: str) -> None:
        self.status_summary.setText(message)

    def export_orders(self) -> None:
        if self.report_service is None:
            return
        destination, _ = QFileDialog.getSaveFileName(self, "Exportar relatório", "ordens.csv", "CSV (*.csv)")
        if destination:
            self.report_service.export_orders_csv(self.report_service.orders(), Path(destination))
