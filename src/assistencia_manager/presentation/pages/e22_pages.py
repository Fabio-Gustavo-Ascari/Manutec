from __future__ import annotations

from decimal import Decimal

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout, QHBoxLayout, QLabel, QPushButton, QSplitter, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from assistencia_manager.application.dto.client import ClientSearchQuery, CreateClientCommand, UpdateClientCommand
from assistencia_manager.application.dto.equipment import EquipmentSearchQuery, CreateEquipmentCommand, UpdateEquipmentCommand
from assistencia_manager.application.dto.procurement import PurchaseReceiptLineCommand, ReceivePurchaseOrderCommand
from assistencia_manager.domain.entities.catalog import CatalogType
from assistencia_manager.presentation.pages.clients import ClientForm, ClientsPage as LegacyClientsPage
from assistencia_manager.presentation.pages.equipment import EquipmentForm, EquipmentPage as LegacyEquipmentPage
from assistencia_manager.presentation.pages.catalogs import CatalogsPage as LegacyCatalogsPage
from assistencia_manager.presentation.pages.purchases import PurchasesPage as LegacyPurchasesPage
from assistencia_manager.presentation.shell import ActionBar, DashboardMetricCard, EmptyState, FilterBar, PageShell


def _table(columns: tuple[str, ...]) -> QTableWidget:
    table = QTableWidget(0, len(columns))
    table.setHorizontalHeaderLabels(columns)
    table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
    table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
    table.horizontalHeader().setStretchLastSection(True)
    return table


class ClientsPage(LegacyClientsPage):
    def __init__(self, service=None, parent=None):
        QWidget.__init__(self, parent)
        self.service = service
        self._items = {}
        self.metric_cards = {
            "total": DashboardMetricCard("Clientes", "0", "base cadastrada", "primary"),
            "active": DashboardMetricCard("Ativos", "0", "prontos para atendimento", "success"),
            "attention": DashboardMetricCard("Atenção", "0", "documentos para revisar", "warning"),
        }
        self.search_input = __import__("PySide6.QtWidgets", fromlist=["QLineEdit"]).QLineEdit()
        self.search_input.setPlaceholderText("Buscar nome, documento ou contato...")
        self.page_input = __import__("PySide6.QtWidgets", fromlist=["QSpinBox"]).QSpinBox(); self.page_input.setMinimum(1)
        search = QPushButton("Buscar"); search.setObjectName("primaryAction"); search.clicked.connect(self.refresh)
        new = QPushButton("Novo cliente"); new.clicked.connect(self.form_clear)
        self.filter_bar = FilterBar(); self.filter_bar.layout.addWidget(self.search_input, 1); self.filter_bar.layout.addWidget(self.page_input); self.filter_bar.layout.addWidget(search); self.filter_bar.layout.addWidget(new)
        self.results_table = _table(("ID", "Nome", "Documento", "Status")); self.results_table.itemSelectionChanged.connect(self._render_detail)
        self.empty_state = EmptyState("Nenhum cliente encontrado", "Ajuste os filtros ou cadastre o primeiro cliente."); self.empty_state.hide()
        self.detail_name_label = QLabel("Selecione um cliente"); self.detail_name_label.setObjectName("detailTitle")
        self.detail_document_label = QLabel("Os dados do cadastro aparecerão aqui.")
        self.form = ClientForm(self); self.form.submitted.connect(self._save_client)
        edit = QPushButton("Editar selecionado"); edit.clicked.connect(self.load_selected)
        deactivate = QPushButton("Inativar selecionado"); deactivate.clicked.connect(self.deactivate_selected)
        actions = ActionBar(); actions.layout.addWidget(edit); actions.layout.addWidget(deactivate)
        detail = QWidget(); detail_layout = QVBoxLayout(detail); detail_layout.addWidget(self.detail_name_label); detail_layout.addWidget(self.detail_document_label); detail_layout.addWidget(self.form); detail_layout.addStretch()
        self.workspace_splitter = QSplitter(Qt.Orientation.Horizontal); left = QWidget(); left_layout = QVBoxLayout(left); left_layout.addWidget(self.results_table); left_layout.addWidget(self.empty_state); left_layout.addWidget(actions); self.workspace_splitter.addWidget(left); self.workspace_splitter.addWidget(detail); self.workspace_splitter.setSizes([650, 420])
        shell = PageShell("Clientes", "Uma visão rápida da base e do cadastro contextual."); shell.body.addWidget(self.filter_bar); metrics = QHBoxLayout(); [metrics.addWidget(card) for card in self.metric_cards.values()]; shell.body.addLayout(metrics); shell.body.addWidget(self.workspace_splitter, 1)
        layout = QVBoxLayout(self); layout.setContentsMargins(18, 18, 18, 18); layout.addWidget(shell)
        self.message = QLabel(); layout.addWidget(self.message)
        self.form.clear_form(); self.refresh()

    def form_clear(self):
        self.form.clear_form(); self.detail_name_label.setText("Novo cliente"); self.detail_document_label.setText("Preencha os dados e salve o cadastro.")

    def refresh(self):
        if self.service is None: return
        result = self.service.search(ClientSearchQuery(search=self.search_input.text().strip() or None, page=self.page_input.value()))
        self._items = {str(item.id): item for item in result.items}; self.results_table.setRowCount(0)
        for item in result.items:
            row = self.results_table.rowCount(); self.results_table.insertRow(row)
            for col, value in enumerate((str(item.id), item.name, item.document or "", item.status.value)): self.results_table.setItem(row, col, QTableWidgetItem(value))
        self.metric_cards["total"].set_value(str(result.total_items)); self.metric_cards["active"].set_value(str(sum(getattr(i.status, "value", "") == "active" for i in result.items))); self.metric_cards["attention"].set_value(str(sum(not getattr(i, "document", None) for i in result.items)))
        self.empty_state.setVisible(not bool(result.items)); self.message.setText(f"{result.total_items} cliente(s) encontrado(s).")

    def _selected(self):
        row = self.results_table.currentRow(); item = self.results_table.item(row, 0) if row >= 0 else None
        return self._items.get(item.text()) if item else None

    def _render_detail(self):
        item = self._selected()
        if item: self.detail_name_label.setText(item.name); self.detail_document_label.setText(item.document or "Documento não informado")

    def load_selected(self):
        item = self._selected()
        if item: self.form.set_client(item); self._render_detail(); self.message.setText("Cliente carregado para edição.")

    def _save_client(self, command):
        if self.service is None: return
        try:
            self.service.update(command) if isinstance(command, UpdateClientCommand) else self.service.create(command); self.form.clear_form(); self.message.setText("Cliente salvo com sucesso."); self.refresh()
        except Exception as error: self.form.error_message.setText(str(error))

    def deactivate_selected(self):
        item = self._selected()
        if item and self.service: self.service.deactivate(item.id); self.refresh(); self.message.setText("Cliente inativado com sucesso.")


class EquipmentPage(LegacyEquipmentPage):
    def __init__(self, service=None, parent=None):
        QWidget.__init__(self, parent); self.service = service; self._items = {}
        self.metric_cards = {"total": DashboardMetricCard("Equipamentos", "0", "ativos", "primary"), "active": DashboardMetricCard("Em operação", "0", "vinculados a clientes", "success"), "attention": DashboardMetricCard("Atenção", "0", "sem número de série", "warning")}
        from PySide6.QtWidgets import QLineEdit, QSpinBox
        self.search_input = QLineEdit(); self.search_input.setPlaceholderText("Buscar tipo, marca, modelo ou série..."); self.page_input = QSpinBox(); self.page_input.setMinimum(1)
        search = QPushButton("Buscar"); search.setObjectName("primaryAction"); search.clicked.connect(self.refresh); new = QPushButton("Novo equipamento"); new.clicked.connect(self.form_clear)
        self.filter_bar = FilterBar(); self.filter_bar.layout.addWidget(self.search_input, 1); self.filter_bar.layout.addWidget(self.page_input); self.filter_bar.layout.addWidget(search); self.filter_bar.layout.addWidget(new)
        self.results_table = _table(("ID", "Tipo", "Marca", "Modelo", "Status")); self.results_table.itemSelectionChanged.connect(self._render_detail); self.empty_state = EmptyState("Nenhum equipamento encontrado", "Cadastre o equipamento recebido para vinculá-lo a uma OS."); self.empty_state.hide()
        self.detail_type_label = QLabel("Selecione um equipamento"); self.detail_type_label.setObjectName("detailTitle"); self.detail_description_label = QLabel("Os dados aparecerão aqui."); self.form = EquipmentForm(self); self.form.submitted.connect(self._save_equipment)
        edit = QPushButton("Editar selecionado"); edit.clicked.connect(self.load_selected); actions = ActionBar(); actions.layout.addWidget(edit)
        detail = QWidget(); dl = QVBoxLayout(detail); dl.addWidget(self.detail_type_label); dl.addWidget(self.detail_description_label); dl.addWidget(self.form); dl.addStretch()
        self.workspace_splitter = QSplitter(Qt.Orientation.Horizontal); left = QWidget(); ll = QVBoxLayout(left); ll.addWidget(self.results_table); ll.addWidget(self.empty_state); ll.addWidget(actions); self.workspace_splitter.addWidget(left); self.workspace_splitter.addWidget(detail)
        shell = PageShell("Equipamentos", "Controle os aparelhos recebidos e seu vínculo com clientes."); shell.body.addWidget(self.filter_bar); metrics = QHBoxLayout(); [metrics.addWidget(card) for card in self.metric_cards.values()]; shell.body.addLayout(metrics); shell.body.addWidget(self.workspace_splitter, 1); layout = QVBoxLayout(self); layout.setContentsMargins(18, 18, 18, 18); layout.addWidget(shell); self.message = QLabel(); layout.addWidget(self.message); self.refresh()

    def form_clear(self): self.form.clear_form(); self.detail_type_label.setText("Novo equipamento")
    def _selected(self):
        row = self.results_table.currentRow(); item = self.results_table.item(row, 0) if row >= 0 else None; return self._items.get(item.text()) if item else None
    def refresh(self):
        if self.service is None: return
        result = self.service.search(EquipmentSearchQuery(search=self.search_input.text().strip() or None, page=self.page_input.value())); self._items = {str(i.id): i for i in result.items}; self.results_table.setRowCount(0)
        for item in result.items:
            row = self.results_table.rowCount(); self.results_table.insertRow(row)
            for col, value in enumerate((str(item.id), item.equipment_type, item.brand or "", item.model or "", item.status.value)): self.results_table.setItem(row, col, QTableWidgetItem(value))
        self.metric_cards["total"].set_value(str(result.total_items)); self.metric_cards["active"].set_value(str(sum(getattr(i.status, "value", "") == "active" for i in result.items))); self.metric_cards["attention"].set_value(str(sum(not getattr(i, "serial_number", None) for i in result.items))); self.empty_state.setVisible(not bool(result.items))
    def _render_detail(self):
        item = self._selected()
        if item: self.detail_type_label.setText(item.equipment_type); self.detail_description_label.setText(" / ".join(filter(None, (item.brand, item.model, item.serial_number))) or "Detalhes não informados")
    def load_selected(self):
        item = self._selected()
        if item: self.form.set_equipment(item); self._render_detail()
    def _save_equipment(self, command):
        if self.service is None: return
        try: self.service.update(command) if isinstance(command, UpdateEquipmentCommand) else self.service.create(command); self.form.clear_form(); self.message.setText("Equipamento salvo com sucesso."); self.refresh()
        except Exception as error: self.form.error_message.setText(str(error))


class CatalogsPage(LegacyCatalogsPage):
    def __init__(self, service=None):
        QWidget.__init__(self); self.service = service; self.active_segment = "Peças"; self.segment_buttons = {}
        self.name_input = __import__("PySide6.QtWidgets", fromlist=["QLineEdit"]).QLineEdit(); self.type_input = __import__("PySide6.QtWidgets", fromlist=["QLineEdit"]).QLineEdit("categoria"); self.search = __import__("PySide6.QtWidgets", fromlist=["QLineEdit"]).QLineEdit(); self.search.setPlaceholderText("Buscar no catálogo..."); self.table = _table(("Tipo", "Nome", "Contato")); self.table.setObjectName("catalogTable")
        self.save_button = QPushButton("Cadastrar"); self.save_button.setObjectName("primaryAction"); self.save_button.clicked.connect(self._save)
        segment_bar = FilterBar()
        for label in ("Peças", "Serviços", "Auxiliares"):
            button = QPushButton(label); button.clicked.connect(lambda checked=False, value=label: self._select_segment(value)); self.segment_buttons[label] = button; segment_bar.layout.addWidget(button)
        segment_bar.layout.addStretch(); segment_bar.layout.addWidget(self.search); self.search.textChanged.connect(self.refresh)
        form = QFormLayout(); form.addRow("Tipo de cadastro", self.type_input); form.addRow("Nome", self.name_input); form.addRow("", self.save_button)
        shell = PageShell("Cadastros", "Peças, serviços e cadastros auxiliares organizados por contexto."); shell.body.addWidget(segment_bar); shell.body.addLayout(form); shell.body.addWidget(self.table, 1); layout = QVBoxLayout(self); layout.setContentsMargins(18, 18, 18, 18); layout.addWidget(shell); self.refresh()
    def _select_segment(self, value): self.active_segment = value; self.refresh()
    def _kind(self): return {"categoria": CatalogType.CATEGORY, "marca": CatalogType.BRAND, "fornecedor": CatalogType.SUPPLIER, "técnico": CatalogType.TECHNICIAN, "tecnico": CatalogType.TECHNICIAN}.get(self.type_input.text().strip().casefold(), CatalogType.CATEGORY)
    def _save(self):
        if not self.service: return
        from assistencia_manager.application.dto.catalog import CreateCatalogCommand
        self.service.create_catalog(CreateCatalogCommand(self._kind(), self.name_input.text().strip())); self.name_input.clear(); self.refresh()
    def refresh(self):
        self.table.setRowCount(0)
        if not self.service: return
        for item in self.service.search_catalogs(self._kind(), self.search.text().strip() or None):
            row = self.table.rowCount(); self.table.insertRow(row); [self.table.setItem(row, col, QTableWidgetItem(value)) for col, value in enumerate((item.kind.value, item.name, item.phone or item.email or ""))]


class PurchasesPage(LegacyPurchasesPage):
    def __init__(self, service=None):
        QWidget.__init__(self); self.service = service; self._orders = {}
        self.metric_cards = {"open": DashboardMetricCard("Pedidos em aberto", "0", "aguardando recebimento", "primary"), "partial": DashboardMetricCard("Recebimento parcial", "0", "exigem conferência", "warning"), "value": DashboardMetricCard("Valor em pedidos", "R$ 0,00", "total comprometido", "success")}
        self.orders_table = _table(("Pedido", "Fornecedor", "Status", "Total")); self.orders_table.itemSelectionChanged.connect(self._select_order); self.empty_state = EmptyState("Nenhum pedido em aberto", "Crie um pedido ou revise as sugestões de reposição."); self.empty_state.hide(); self.receipt_quantity_input = __import__("PySide6.QtWidgets", fromlist=["QLineEdit"]).QLineEdit(); self.receipt_quantity_input.setPlaceholderText("Quantidade recebida"); self.receive_button = QPushButton("Registrar recebimento"); self.receive_button.setObjectName("primaryAction"); self.receive_button.clicked.connect(self._receive); self.message_label = QLabel()
        panel = QWidget(); pl = QVBoxLayout(panel); self.selected_order_label = QLabel("Selecione um pedido"); self.selected_order_label.setObjectName("detailTitle"); pl.addWidget(self.selected_order_label); pl.addWidget(self.receipt_quantity_input); pl.addWidget(self.receive_button); pl.addWidget(self.message_label); pl.addStretch()
        self.workspace_splitter = QSplitter(Qt.Orientation.Horizontal); left = QWidget(); ll = QVBoxLayout(left); ll.addWidget(self.orders_table); ll.addWidget(self.empty_state); self.workspace_splitter.addWidget(left); self.workspace_splitter.addWidget(panel)
        shell = PageShell("Compras", "Acompanhe pedidos, recebimentos e o impacto no estoque."); metrics = QHBoxLayout(); [metrics.addWidget(card) for card in self.metric_cards.values()]; shell.body.addLayout(metrics); shell.body.addWidget(self.workspace_splitter, 1); layout = QVBoxLayout(self); layout.setContentsMargins(18, 18, 18, 18); layout.addWidget(shell); self.refresh()
    def refresh(self):
        if self.service is None: return
        orders = tuple(self.service.list_orders()) if hasattr(self.service, "list_orders") else ()
        self._orders = {str(order.id): order for order in orders}; self.orders_table.setRowCount(0)
        for order in orders:
            row = self.orders_table.rowCount(); self.orders_table.insertRow(row); [self.orders_table.setItem(row, col, QTableWidgetItem(value)) for col, value in enumerate((str(order.id)[:8], str(order.supplier_id)[:8], order.status.value.replace("_", " "), f"R$ {order.total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")))]
        self.metric_cards["open"].set_value(str(sum(order.status.value not in ("received", "cancelled") for order in orders))); self.metric_cards["partial"].set_value(str(sum(order.status.value == "partially_received" for order in orders))); self.metric_cards["value"].set_value(f"R$ {sum((order.total for order in orders), Decimal('0')):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")); self.empty_state.setVisible(not bool(orders))
    def _selected(self):
        row = self.orders_table.currentRow(); item = self.orders_table.item(row, 0) if row >= 0 else None; return self._orders.get(next((key for key in self._orders if key.startswith(item.text())), "")) if item else None
    def _select_order(self):
        order = self._selected()
        if order: self.selected_order_label.setText(f"Pedido {str(order.id)[:8]} — {order.status.value}")
    def _receive(self):
        order = self._selected()
        if not order or self.service is None: return
        quantity = Decimal(self.receipt_quantity_input.text().strip()); line = order.lines[0]
        self.service.receive(ReceivePurchaseOrderCommand(order.id, (PurchaseReceiptLineCommand(line.part_id, quantity),))); self.message_label.setText("Recebimento registrado com sucesso."); self.refresh()
