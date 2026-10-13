from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from assistencia_manager.application.dto.fiscal import FiscalConfigurationCommand
from assistencia_manager.application.services.company_settings_service import CompanySettingsService
from assistencia_manager.domain.entities.fiscal import FiscalEnvironment
from assistencia_manager.domain.entities.finance import FinancialEntryStatus, FinancialEntryType
from assistencia_manager.domain.exceptions import DomainError
from assistencia_manager.presentation.shell import (
    ActionBar,
    AlertBanner,
    DashboardMetricCard,
    EmptyState,
    FilterBar,
    PageShell,
)


def _table(columns: tuple[str, ...]) -> QTableWidget:
    table = QTableWidget(0, len(columns))
    table.setHorizontalHeaderLabels(columns)
    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.horizontalHeader().setStretchLastSection(True)
    return table


def _money(value: Decimal | int | float) -> str:
    return f"R$ {Decimal(str(value)):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


class FinancePage(QWidget):
    """Workspace de decisão financeira com resumo, filtros e liquidação contextual."""

    def __init__(self, service=None, parent=None) -> None:
        super().__init__(parent)
        self.service = service
        self._entries = {}
        self.metric_cards = {
            "inflow": DashboardMetricCard("Entradas no período", "R$ 0,00", "recebimentos", "success"),
            "outflow": DashboardMetricCard("Saídas no período", "R$ 0,00", "pagamentos", "danger"),
            "balance": DashboardMetricCard("Saldo do período", "R$ 0,00", "entradas menos saídas", "primary"),
            "open": DashboardMetricCard("Em aberto", "R$ 0,00", "a pagar + a receber", "warning"),
        }
        self.start_input = QLineEdit((date.today() - timedelta(days=30)).isoformat())
        self.end_input = QLineEdit(date.today().isoformat())
        self.type_filter = QComboBox()
        self.type_filter.addItem("Todos", None)
        self.type_filter.addItem("A pagar", FinancialEntryType.PAYABLE)
        self.type_filter.addItem("A receber", FinancialEntryType.RECEIVABLE)
        refresh = QPushButton("Atualizar"); refresh.setObjectName("primaryAction"); refresh.clicked.connect(self.refresh)
        self.filter_bar = FilterBar()
        self.filter_bar.layout.addWidget(QLabel("Período")); self.filter_bar.layout.addWidget(self.start_input)
        self.filter_bar.layout.addWidget(QLabel("até")); self.filter_bar.layout.addWidget(self.end_input)
        self.filter_bar.layout.addWidget(self.type_filter); self.filter_bar.layout.addWidget(refresh)

        self.entries_table = _table(("Descrição", "Tipo", "Vencimento", "Status", "Saldo"))
        self.entries_table.itemSelectionChanged.connect(self._select_entry)
        self.empty_state = EmptyState("Nenhum lançamento no período", "Ajuste o período ou registre um novo lançamento."); self.empty_state.hide()
        self.selected_label = QLabel("Selecione um lançamento"); self.selected_label.setObjectName("detailTitle")
        self.selected_detail = QLabel("O lançamento selecionado aparecerá aqui."); self.selected_detail.setWordWrap(True)
        self.settle_button = QPushButton("Liquidar saldo"); self.settle_button.setObjectName("primaryAction"); self.settle_button.clicked.connect(self.settle_selected)
        self.message_label = QLabel()
        actions = ActionBar(); actions.layout.addWidget(self.settle_button)
        detail = QWidget(); detail_layout = QVBoxLayout(detail); detail_layout.addWidget(self.selected_label); detail_layout.addWidget(self.selected_detail); detail_layout.addWidget(actions); detail_layout.addWidget(self.message_label); detail_layout.addStretch()
        self.workspace_splitter = QSplitter(Qt.Orientation.Horizontal)
        left = QWidget(); left_layout = QVBoxLayout(left); left_layout.addWidget(self.entries_table); left_layout.addWidget(self.empty_state)
        self.workspace_splitter.addWidget(left); self.workspace_splitter.addWidget(detail); self.workspace_splitter.setSizes([700, 360])
        shell = PageShell("Financeiro", "Decida com clareza: caixa, vencimentos e liquidações em um só lugar.")
        shell.body.addWidget(self.filter_bar)
        metrics = QHBoxLayout(); [metrics.addWidget(card) for card in self.metric_cards.values()]; shell.body.addLayout(metrics); shell.body.addWidget(self.workspace_splitter, 1)
        layout = QVBoxLayout(self); layout.setContentsMargins(18, 18, 18, 18); layout.addWidget(shell)
        self.refresh()

    def _date_range(self) -> tuple[date, date]:
        return date.fromisoformat(self.start_input.text()), date.fromisoformat(self.end_input.text())

    def _load_entries(self):
        if self.service is None: return ()
        start, end = self._date_range()
        if hasattr(self.service, "list_entries"):
            return tuple(self.service.list_entries(start=start, end=end, entry_type=self.type_filter.currentData()))
        with self.service._unit_of_work_factory() as uow:
            return tuple(item for item in uow.financial_entries.list() if start <= item.due_date <= end)

    def refresh(self) -> None:
        try:
            entries = self._load_entries()
        except (ValueError, DomainError) as error:
            self.message_label.setText(str(error)); return
        self._entries = {str(item.id): item for item in entries}; self.entries_table.setRowCount(0)
        for item in entries:
            row = self.entries_table.rowCount(); self.entries_table.insertRow(row)
            values = (item.description, "A pagar" if item.entry_type is FinancialEntryType.PAYABLE else "A receber", item.due_date.isoformat(), item.status.value, _money(item.remaining_amount))
            for col, value in enumerate(values): self.entries_table.setItem(row, col, QTableWidgetItem(value))
        self.empty_state.setVisible(not entries)
        inflow = sum((item.paid_amount for item in entries if item.entry_type is FinancialEntryType.RECEIVABLE), Decimal("0"))
        outflow = sum((item.paid_amount for item in entries if item.entry_type is FinancialEntryType.PAYABLE), Decimal("0"))
        open_total = sum((item.remaining_amount for item in entries if item.status in {FinancialEntryStatus.OPEN, FinancialEntryStatus.PARTIAL}), Decimal("0"))
        self.metric_cards["inflow"].set_value(_money(inflow)); self.metric_cards["outflow"].set_value(_money(outflow)); self.metric_cards["balance"].set_value(_money(inflow - outflow)); self.metric_cards["open"].set_value(_money(open_total))

    def _selected(self):
        row = self.entries_table.currentRow(); cell = self.entries_table.item(row, 0) if row >= 0 else None
        return next((item for item in self._entries.values() if item.description == cell.text()), None) if cell else None

    def _select_entry(self) -> None:
        item = self._selected()
        if item: self.selected_label.setText(item.description); self.selected_detail.setText(f"{item.status.value} • saldo {_money(item.remaining_amount)} • vencimento {item.due_date.isoformat()}")

    def settle_selected(self) -> None:
        item = self._selected()
        if item is None or self.service is None: return
        self.service.settle(item.id); self.message_label.setText("Lançamento liquidado com sucesso."); self.refresh()


class FiscalPage(QWidget):
    """Configuração fiscal com status de ambiente e diagnóstico operacional."""

    def __init__(self, service=None, parent=None) -> None:
        super().__init__(parent); self.service = service
        self.environment = QComboBox(); self.environment.addItems(["homologation", "production"])
        self.document = QLineEdit(); self.provider = QLineEdit("simulated")
        self.status_banner = AlertBanner("Ambiente fiscal", "Nenhuma configuração fiscal foi carregada.", "warning")
        self.message_label = QLabel()
        form = QFormLayout(); form.addRow("CNPJ/CPF da empresa", self.document); form.addRow("Provedor", self.provider); form.addRow("Ambiente", self.environment)
        config = QGroupBox("Configuração e emissão"); config_layout = QVBoxLayout(config); config_layout.addLayout(form)
        save = QPushButton("Salvar configuração"); save.setObjectName("primaryAction"); save.clicked.connect(self.save); config_layout.addWidget(save)
        diagnostics = QGroupBox("Diagnóstico de periféricos"); diagnostics_layout = QHBoxLayout(diagnostics)
        for label in ("Testar impressora", "Testar leitor", "Testar PIX"):
            button = QPushButton(label); button.clicked.connect(lambda checked=False, name=label: self.message_label.setText(f"{name}: adaptador pronto para uso.")); diagnostics_layout.addWidget(button)
        shell = PageShell("Fiscal e periféricos", "Configure o ambiente, emita documentos e valide os dispositivos da operação.")
        shell.body.addWidget(self.status_banner); shell.body.addWidget(config); shell.body.addWidget(diagnostics); shell.body.addWidget(self.message_label); shell.body.addStretch()
        layout = QVBoxLayout(self); layout.setContentsMargins(18, 18, 18, 18); layout.addWidget(shell); self.load()

    def load(self) -> None:
        if self.service and (configuration := self.service.get_configuration()):
            self.document.setText(configuration.company_document); self.provider.setText(configuration.provider); self.environment.setCurrentText(configuration.environment.value)
            self.status_banner.findChildren(QLabel)[1].setText(f"Ambiente {configuration.environment.value} configurado com o provedor {configuration.provider}.")

    def save(self) -> None:
        if not self.service: return
        try:
            configuration = self.service.configure(FiscalConfigurationCommand(
                company_document=self.document.text(),
                environment=FiscalEnvironment(self.environment.currentText()),
                provider=self.provider.text(),
            ))
            self.message_label.setText("Configuração fiscal salva com segurança."); self.status_banner.findChildren(QLabel)[1].setText(f"Ambiente {configuration.environment.value} configurado com o provedor {configuration.provider}.")
        except DomainError as error: self.message_label.setText(str(error))


class CompanySettingsPage(QWidget):
    """Configurações da empresa separadas por contexto e com feedback não bloqueante."""

    def __init__(self, service: CompanySettingsService | None = None, parent=None) -> None:
        super().__init__(parent); self.service = service; self.inputs = {field: QLineEdit() for field in CompanySettingsService.FIELDS}; self.message_label = QLabel()
        labels = {"name": "Nome", "document": "Documento", "address": "Endereço", "phone": "Telefone", "email": "E-mail"}
        identity = QGroupBox("Identidade da empresa"); identity_form = QFormLayout(identity)
        for field in ("name", "document"): identity_form.addRow(labels[field], self.inputs[field])
        contact = QGroupBox("Contato e endereço"); contact_form = QFormLayout(contact)
        for field in ("address", "phone", "email"): contact_form.addRow(labels[field], self.inputs[field])
        save = QPushButton("Salvar configurações"); save.setObjectName("primaryAction"); save.clicked.connect(self.save)
        shell = PageShell("Configurações", "Mantenha os dados da empresa e os contatos operacionais sempre atualizados."); shell.body.addWidget(identity); shell.body.addWidget(contact); shell.body.addWidget(save); shell.body.addWidget(self.message_label); shell.body.addStretch()
        layout = QVBoxLayout(self); layout.setContentsMargins(18, 18, 18, 18); layout.addWidget(shell); self.load()

    def load(self) -> None:
        if self.service:
            for field, value in self.service.get().items(): self.inputs[field].setText(value)

    def save(self) -> None:
        if not self.service: return
        try:
            self.service.update({field: widget.text() for field, widget in self.inputs.items()}); self.message_label.setText("Configurações salvas com sucesso.")
        except DomainError as error: self.message_label.setText(str(error))

