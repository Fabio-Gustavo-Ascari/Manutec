from __future__ import annotations

import re
from datetime import date
from decimal import Decimal
from pathlib import Path

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDateEdit, QFileDialog, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout,
    QWidget,
)

from assistencia_manager.application.services.report_service import ReportFilters
from assistencia_manager.domain.entities.access import Permission, UserRole
from assistencia_manager.presentation.shell import DashboardMetricCard, FilterBar, PageShell


def _money(value: object) -> str:
    try:
        return f"R$ {Decimal(str(value or 0)):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except (ArithmeticError, ValueError):
        return "R$ 0,00"


def _display(value: object) -> str:
    if value is None:
        return "—"
    return getattr(value, "value", str(value))


def _masked(value: object) -> str:
    text = "" if value is None else str(value)
    markers = r"senha|password|token|document|telefone|phone|email"
    pattern = re.compile(
        rf"(?P<prefix>[\"']?(?:{markers})[\"']?\s*[:=]\s*[\"']?)(?P<secret>[^\"'\s,}}]+)",
        re.IGNORECASE,
    )
    return pattern.sub(lambda match: f"{match.group('prefix')}••••", text)


class ReportsPage(PageShell):
    def __init__(self, report_service=None, parent=None):
        self.report_service = report_service
        self.kind_filter = QComboBox(); self.kind_filter.addItems(("work_orders", "sales", "inventory", "purchases", "finance", "margin", "productivity", "warranties"))
        self.status_filter = QComboBox()
        for label, value in (("Todos", ""), ("Em aberto", "open"), ("Concluído", "completed"), ("Entregue", "delivered"), ("Cancelado", "cancelled"), ("Pago", "paid"), ("Pendente", "pending")):
            self.status_filter.addItem(label, value)
        self.search_input = QLineEdit(); self.search_input.setPlaceholderText("Buscar por texto…")
        self.start_date = QDateEdit(QDate.currentDate()); self.start_date.setCalendarPopup(True); self.start_date.setSpecialValueText("Sem início")
        self.end_date = QDateEdit(QDate.currentDate()); self.end_date.setCalendarPopup(True); self.end_date.setSpecialValueText("Sem fim")
        self.metric_cards = {key: DashboardMetricCard(label, "0") for key, label in (("records", "Registros"), ("total", "Total"), ("average", "Média"))}
        self.results_table = QTableWidget(); self.results_table.setSortingEnabled(True); self.results_table.setAlternatingRowColors(True)
        self.page_size = QComboBox(); self.page_size.addItems(("10", "25", "50")); self.page_label = QLabel("Página 1 de 1")
        self.previous_page = QPushButton("Anterior"); self.next_page = QPushButton("Próxima")
        self.previous_page.clicked.connect(lambda: self._change_page(-1)); self.next_page.clicked.connect(lambda: self._change_page(1)); self.page_size.currentTextChanged.connect(lambda: self._render_page())
        self.message_label = QLabel("Ajuste os filtros para consultar o relatório.")
        super().__init__("Relatórios", "Indicadores, resultados e exportações em um só lugar.", parent, actions=(QPushButton("Exportar CSV"), QPushButton("Exportar PDF")))
        self.export_csv_button, self.export_pdf_button = self.header_layout.itemAt(self.header_layout.count() - 2).widget(), self.header_layout.itemAt(self.header_layout.count() - 1).widget()
        self.export_csv_button.clicked.connect(lambda: self.export("csv")); self.export_pdf_button.clicked.connect(lambda: self.export("pdf"))
        filters = FilterBar(); form = QFormLayout(); form.addRow("Relatório", self.kind_filter); form.addRow("Status", self.status_filter); form.addRow("Busca", self.search_input); form.addRow("De", self.start_date); form.addRow("Até", self.end_date); filters.layout.addLayout(form)
        refresh = QPushButton("Atualizar"); refresh.clicked.connect(self.refresh); filters.layout.addWidget(refresh)
        metrics = QHBoxLayout()
        for card in self.metric_cards.values(): metrics.addWidget(card)
        pagination = QHBoxLayout(); pagination.addWidget(QLabel("Linhas por página")); pagination.addWidget(self.page_size); pagination.addStretch(); pagination.addWidget(self.previous_page); pagination.addWidget(self.page_label); pagination.addWidget(self.next_page)
        self.body.addWidget(filters); self.body.addLayout(metrics); self.body.addWidget(self.results_table); self.body.addLayout(pagination); self.body.addWidget(self.message_label)
        self.kind_filter.currentIndexChanged.connect(self.refresh); self.status_filter.currentIndexChanged.connect(self.refresh); self.search_input.textChanged.connect(self.refresh)
        self.refresh()

    def _filters(self) -> ReportFilters:
        return ReportFilters(search=self.search_input.text().strip() or None, status=self.status_filter.currentData() or None,
                             start=self.start_date.date().toPython() if self.start_date.date() != QDate.currentDate() else None,
                             end=self.end_date.date().toPython() if self.end_date.date() != QDate.currentDate() else None)

    def refresh(self) -> None:
        if self.report_service is None:
            return
        result = self.report_service.generate(self.kind_filter.currentData() or self.kind_filter.currentText(), self._filters())
        self._all_rows = result.rows; self._last_result = result; self._page = 0
        self._render_page()
        total = sum((Decimal(str(row.get("total", row.get("amount", 0)) or 0)) for row in result.rows), Decimal("0"))
        average = total / len(result.rows) if result.rows else Decimal("0")
        self.metric_cards["records"].set_value(str(len(result.rows))); self.metric_cards["total"].set_value(_money(total)); self.metric_cards["average"].set_value(_money(average))
        self.message_label.setText(f"{len(result.rows)} registro(s) encontrado(s).")

    def _render_page(self) -> None:
        rows = getattr(self, "_all_rows", ())
        size = int(self.page_size.currentText()); pages = max(1, (len(rows) + size - 1) // size); self._page = min(getattr(self, "_page", 0), pages - 1)
        self.results_table.setSortingEnabled(False); self.results_table.clear(); self.results_table.setColumnCount(len(self._last_result.columns)); self.results_table.setHorizontalHeaderLabels(self._last_result.columns); self.results_table.setRowCount(min(size, len(rows) - self._page * size))
        for row_index, row in enumerate(rows[self._page * size:(self._page + 1) * size]):
            for column_index, column in enumerate(self._last_result.columns):
                item = QTableWidgetItem(_display(row.get(column))); item.setData(Qt.ItemDataRole.UserRole, row.get(column)); self.results_table.setItem(row_index, column_index, item)
        self.results_table.setSortingEnabled(True)
        self.page_label.setText(f"Página {self._page + 1} de {pages}"); self.previous_page.setEnabled(self._page > 0); self.next_page.setEnabled(self._page < pages - 1)

    def _change_page(self, delta: int) -> None:
        self._page = max(0, getattr(self, "_page", 0) + delta); self._render_page()

    def export(self, extension: str) -> None:
        if self.report_service is None or not hasattr(self, "_last_result"):
            return
        destination, _ = QFileDialog.getSaveFileName(self, "Exportar relatório", f"relatorio.{extension}", f"{extension.upper()} (*.{extension})")
        if not destination:
            return
        path = (self.report_service.export_csv(self._last_result, Path(destination)) if extension == "csv" else self.report_service.export_pdf(self._last_result, Path(destination)))
        self.message_label.setText(f"Exportado: {path.name}")


class AccessAuditPage(PageShell):
    def __init__(self, access_service=None, audit_service=None, parent=None):
        self.access_service, self.audit_service = access_service, audit_service
        self.create_name = QLineEdit(); self.create_name.setPlaceholderText("Nome")
        self.create_username = QLineEdit(); self.create_username.setPlaceholderText("Usuário")
        self.create_credential = QLineEdit(); self.create_credential.setPlaceholderText("Senha (mín. 8 caracteres)"); self.create_credential.setEchoMode(QLineEdit.EchoMode.Password)
        self.create_role = QComboBox(); [self.create_role.addItem(role.value.title(), role) for role in UserRole]
        self.create_button = QPushButton("Criar usuário"); self.create_button.clicked.connect(self.create_user)
        self.role_filter = QComboBox(); self.role_filter.addItem("Todos", "")
        for role in UserRole: self.role_filter.addItem(role.value.title(), role)
        self.audit_module = QLineEdit(); self.audit_module.setPlaceholderText("Filtrar módulo")
        self.action_filter = QLineEdit(); self.action_filter.setPlaceholderText("Filtrar ação")
        self.user_table = QTableWidget(); self.user_table.setColumnCount(4); self.user_table.setHorizontalHeaderLabels(("Usuário", "Nome", "Perfil", "Ativo")); self.user_table.setSortingEnabled(True)
        self.audit_table = QTableWidget(); self.audit_table.setColumnCount(5); self.audit_table.setHorizontalHeaderLabels(("Data", "Módulo", "Ação", "Usuário", "Detalhes")); self.audit_table.setSortingEnabled(True)
        self.permission_checks = {key: QCheckBox(key) for key in ("reports:view", "reports:export", "sales:view", "inventory:view", "finance:view", "users:manage")}
        self.message_label = QLabel()
        super().__init__("Usuários e auditoria", "Perfis, permissões e histórico de alterações com dados sensíveis protegidos.", parent)
        creation = FilterBar(); [creation.layout.addWidget(field) for field in (self.create_name, self.create_username, self.create_credential, self.create_role)]; creation.layout.addWidget(self.create_button)
        user_filters = FilterBar(); user_filters.layout.addWidget(QLabel("Perfil")); user_filters.layout.addWidget(self.role_filter); refresh = QPushButton("Atualizar"); refresh.clicked.connect(self.refresh); user_filters.layout.addWidget(refresh)
        permission_bar = FilterBar(); permission_bar.layout.addWidget(QLabel("Permissões do usuário selecionado")); [permission_bar.layout.addWidget(check) for check in self.permission_checks.values()]; save = QPushButton("Salvar permissões"); save.clicked.connect(self.save_permissions); permission_bar.layout.addWidget(save)
        audit_filters = FilterBar(); audit_filters.layout.addWidget(QLabel("Módulo")); audit_filters.layout.addWidget(self.audit_module); audit_filters.layout.addWidget(QLabel("Ação")); audit_filters.layout.addWidget(self.action_filter); audit_refresh = QPushButton("Filtrar histórico"); audit_refresh.clicked.connect(self.refresh_audit); audit_filters.layout.addWidget(audit_refresh)
        self.body.addWidget(creation); self.body.addWidget(user_filters); self.body.addWidget(self.user_table); self.body.addWidget(permission_bar); self.body.addWidget(audit_filters); self.body.addWidget(self.audit_table); self.body.addWidget(self.message_label)
        self.user_table.itemSelectionChanged.connect(self._load_permissions); self.refresh()

    def refresh(self) -> None:
        if self.access_service is not None:
            users = tuple(user for user in self.access_service.list_users() if not self.role_filter.currentData() or user.role is self.role_filter.currentData())
            self.user_table.setSortingEnabled(False); self.user_table.setRowCount(len(users)); self._users = users
            for row, user in enumerate(users):
                values = (user.username, user.display_name, user.role.value, "Sim" if user.active else "Não")
                for column, value in enumerate(values): self.user_table.setItem(row, column, QTableWidgetItem(str(value)))
            self.user_table.setSortingEnabled(True)
        self.refresh_audit()

    def refresh_audit(self) -> None:
        if self.audit_service is None: return
        module = self.audit_module.text().strip() or None; action = self.action_filter.text().strip() or None; entries = self.audit_service.list(module=module, action=action)
        self.audit_table.setSortingEnabled(False); self.audit_table.setRowCount(len(entries))
        for row, entry in enumerate(entries):
            values = (getattr(entry.created_at, "isoformat", lambda: str(entry.created_at))(), entry.module, entry.action, str(entry.user_id or "—"), _masked(entry.details))
            for column, value in enumerate(values): self.audit_table.setItem(row, column, QTableWidgetItem(value))
        self.audit_table.setSortingEnabled(True)

    def create_user(self) -> None:
        if self.access_service is None: return
        try:
            self.access_service.create_user(self.create_name.text(), self.create_username.text(), self.create_credential.text(), self.create_role.currentData())
            self.message_label.setText("Usuário criado com segurança."); self.create_name.clear(); self.create_username.clear(); self.create_credential.clear(); self.refresh()
        except Exception as error:
            self.message_label.setText(str(error))

    def _load_permissions(self) -> None:
        if not self.user_table.selectedItems(): return
        user = self._users[self.user_table.currentRow()]
        for key, check in self.permission_checks.items(): check.setChecked(key in user.permissions)

    def save_permissions(self) -> None:
        if self.access_service is None or not self.user_table.selectedItems(): return
        user = self._users[self.user_table.currentRow()]; permissions = {Permission(*key.split(":", 1)) for key, check in self.permission_checks.items() if check.isChecked()}
        self.access_service.set_permissions(user.id, permissions); self.message_label.setText("Permissões salvas com segurança.")
