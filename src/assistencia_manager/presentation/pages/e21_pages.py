from __future__ import annotations

from decimal import Decimal, InvalidOperation

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QComboBox, QFrame, QGridLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit,
    QMessageBox, QPushButton, QSplitter, QTabWidget, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from assistencia_manager.application.dto.client import ClientSearchQuery
from assistencia_manager.application.dto.equipment import EquipmentSearchQuery
from assistencia_manager.application.dto.inventory import (
    CreatePartCommand, PartSearchQuery, RecordInventoryMovementCommand,
)
from assistencia_manager.application.dto.sales import (
    AddSaleItemCommand, CreateSaleCommand, RecordPaymentCommand,
)
from assistencia_manager.application.dto.work_order import (
    AddWorkOrderItemCommand, OpenWorkOrderCommand, UpdateWorkOrderDetailsCommand,
    WorkOrderEvidenceCommand, WorkOrderSearchQuery, WorkOrderStatusCommand,
)
from assistencia_manager.domain.entities.inventory import InventoryMovementType
from assistencia_manager.domain.entities.sales import PaymentMethod
from assistencia_manager.domain.entities.work_order import WorkOrderPriority, WorkOrderStatus
from assistencia_manager.domain.exceptions import DomainError
from assistencia_manager.presentation.shell import (
    DashboardMetricCard, EmptyState, FilterBar, PageShell, SearchableComboBox,
    populate_combo,
)


def _table(table: QTableWidget, values: tuple[object, ...]) -> None:
    row = table.rowCount()
    table.insertRow(row)
    for column, value in enumerate(values):
        table.setItem(row, column, QTableWidgetItem(str(value)))


def _panel(name: str = "operationPanel") -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName(name)
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(16, 16, 16, 16)
    layout.setSpacing(12)
    return frame, layout


def _section(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("sectionTitle")
    return label


def _money(value: object) -> str:
    amount = Decimal(str(value)).quantize(Decimal("0.01"))
    return f"R$ {amount:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")


def _status_text(status: WorkOrderStatus) -> str:
    return {
        WorkOrderStatus.OPEN: "Aberta",
        WorkOrderStatus.UNDER_ANALYSIS: "Em análise",
        WorkOrderStatus.QUOTE_SENT: "Orçamento enviado",
        WorkOrderStatus.APPROVED: "Aprovada",
        WorkOrderStatus.REJECTED: "Rejeitada",
        WorkOrderStatus.IN_PROGRESS: "Em execução",
        WorkOrderStatus.COMPLETED: "Concluída",
        WorkOrderStatus.DELIVERED: "Entregue",
        WorkOrderStatus.CANCELLED: "Cancelada",
    }[status]


class WorkOrdersPage(QWidget):
    def __init__(self, service=None, client_service=None, equipment_service=None):
        super().__init__()
        self.service = service
        self.client_service = client_service
        self.equipment_service = equipment_service
        self._orders: dict[str, object] = {}

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por defeito, cliente ou número da OS")
        self.status_filter = QComboBox()
        self.status_filter.addItem("Todos os status", None)
        for status in WorkOrderStatus:
            self.status_filter.addItem(_status_text(status), status)
        self.client_label = QLabel("Cliente")
        self.client_input = SearchableComboBox()
        self.equipment_input = SearchableComboBox()
        self.issue_input = QLineEdit()
        self.issue_input.setPlaceholderText("Defeito relatado")
        self.priority_input = QComboBox()
        for priority in WorkOrderPriority:
            self.priority_input.addItem(priority.value.title(), priority)
        self.technician_input = QLineEdit()
        self.origin_input = QLineEdit("counter")
        self.checklist_input = QLineEdit()
        self.checklist_input.setPlaceholderText("Checklist separado por vírgulas")
        self.observations_input = QLineEdit()
        self.observations_input.setPlaceholderText("Observações")
        self.diagnosis_input = QLineEdit()
        self.diagnosis_input.setPlaceholderText("Diagnóstico")
        self.photo_input = QLineEdit()
        self.photo_input.setPlaceholderText("Foto")
        self.attachment_input = QLineEdit()
        self.attachment_input.setPlaceholderText("Anexo")
        self.report_input = QLineEdit()
        self.report_input.setPlaceholderText("Laudo")
        self.item_description = QLineEdit()
        self.item_description.setPlaceholderText("Serviço ou peça")
        self.item_quantity = QLineEdit("1")
        self.item_price = QLineEdit("0")

        self.orders_table = QTableWidget(0, 4)
        self.orders_table.setHorizontalHeaderLabels(["OS", "Status", "Defeito", "Total"])
        self.orders_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.orders_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.orders_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.items_table = QTableWidget(0, 4)
        self.items_table.setHorizontalHeaderLabels(["Item", "Qtd.", "Unitário", "Total"])
        self.items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)

        self.open_button = QPushButton("Abrir ordem")
        self.open_button.setObjectName("primaryAction")
        self.add_item_button = QPushButton("Adicionar item")
        self.refresh_button = QPushButton("Atualizar")
        self.approve_button = QPushButton("Aprovar")
        self.cancel_button = QPushButton("Cancelar")
        self.update_button = QPushButton("Salvar detalhes")

        self.summary_cards = {
            "total": DashboardMetricCard("Ordens encontradas", "0", "resultado dos filtros"),
            "open": DashboardMetricCard("Em atendimento", "0", "ordens ativas", "success"),
            "attention": DashboardMetricCard("Aguardando decisão", "0", "orçamentos enviados", "warning"),
        }
        summary = QHBoxLayout()
        for card in self.summary_cards.values():
            summary.addWidget(card)
        filters = FilterBar()
        filters.layout.addWidget(self.search_input, 2)
        filters.layout.addWidget(self.status_filter)
        filters.layout.addWidget(self.refresh_button)

        list_panel, list_layout = _panel()
        list_layout.addWidget(_section("Fila de atendimento"))
        list_layout.addWidget(self.orders_table, 1)

        self.detail_panel, detail_layout = _panel()
        self.detail_order_label = QLabel("OS —")
        self.detail_order_label.setObjectName("detailTitle")
        self.detail_status_label = QLabel("Nenhuma ordem selecionada")
        self.detail_status_label.setObjectName("statusPill")
        heading = QHBoxLayout()
        heading.addWidget(self.detail_order_label)
        heading.addStretch()
        heading.addWidget(self.detail_status_label)
        detail_layout.addLayout(heading)
        actions = QHBoxLayout()
        actions.addWidget(self.approve_button)
        actions.addWidget(self.cancel_button)
        actions.addStretch()
        detail_layout.addLayout(actions)
        detail_layout.addWidget(_section("Itens e serviços"))
        detail_layout.addWidget(self.items_table, 1)
        item_row = QHBoxLayout()
        item_row.addWidget(self.item_description, 2)
        item_row.addWidget(self.item_quantity)
        item_row.addWidget(self.item_price)
        item_row.addWidget(self.add_item_button)
        detail_layout.addLayout(item_row)
        evidence = QGridLayout()
        evidence.addWidget(self.diagnosis_input, 0, 0, 1, 2)
        evidence.addWidget(self.observations_input, 0, 2, 1, 2)
        evidence.addWidget(self.photo_input, 1, 0)
        evidence.addWidget(self.attachment_input, 1, 1)
        evidence.addWidget(self.report_input, 1, 2)
        evidence.addWidget(self.update_button, 1, 3)
        detail_layout.addLayout(evidence)
        self.empty_state = EmptyState(
            "Selecione uma ordem", "Detalhes, itens e ações aparecerão aqui."
        )
        detail_host, detail_host_layout = _panel()
        detail_host_layout.setContentsMargins(0, 0, 0, 0)
        detail_host_layout.addWidget(self.empty_state)
        detail_host_layout.addWidget(self.detail_panel, 1)
        self.detail_panel.hide()

        self.workspace_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.workspace_splitter.addWidget(list_panel)
        self.workspace_splitter.addWidget(detail_host)
        self.workspace_splitter.setSizes([440, 620])
        self.workspace_splitter.setStretchFactor(0, 2)
        self.workspace_splitter.setStretchFactor(1, 3)

        new_order = QWidget()
        grid = QGridLayout(new_order)
        compact_fields = (
            ("Cliente", self.client_input), ("Equipamento", self.equipment_input),
            ("Prioridade", self.priority_input), ("Técnico", self.technician_input),
        )
        for column, (label, field) in enumerate(compact_fields):
            grid.addWidget(QLabel(label), 0, column)
            grid.addWidget(field, 1, column)
        grid.addWidget(self.issue_input, 2, 0, 1, 2)
        grid.addWidget(self.checklist_input, 2, 2)
        grid.addWidget(self.origin_input, 2, 3)
        grid.addWidget(self.open_button, 3, 3)
        operation = QWidget()
        operation_layout = QVBoxLayout(operation)
        operation_layout.setContentsMargins(0, 8, 0, 0)
        operation_layout.addWidget(self.workspace_splitter)
        self.operation_tabs = QTabWidget()
        self.operation_tabs.addTab(operation, "Atendimento")
        self.operation_tabs.addTab(new_order, "Nova ordem")

        self.page_shell = PageShell(
            "Ordens de serviço", "Fila, orçamento e execução em um único espaço"
        )
        self.page_shell.body.addLayout(summary)
        self.page_shell.body.addWidget(filters)
        self.page_shell.body.addWidget(self.operation_tabs, 1)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.addWidget(self.page_shell)

        self.orders_table.itemSelectionChanged.connect(self._show_selected)
        self.client_input.currentIndexChanged.connect(self._load_equipment)
        self.search_input.textChanged.connect(self.refresh)
        self.status_filter.currentIndexChanged.connect(self.refresh)
        self.open_button.clicked.connect(self._open)
        self.add_item_button.clicked.connect(self._add_item)
        self.refresh_button.clicked.connect(self.refresh)
        self.approve_button.clicked.connect(lambda: self._transition(WorkOrderStatus.APPROVED))
        self.cancel_button.clicked.connect(lambda: self._transition(WorkOrderStatus.CANCELLED))
        self.update_button.clicked.connect(self._update_details)
        self._load_clients()
        self.refresh()

    def _load_clients(self) -> None:
        if self.client_service:
            try:
                populate_combo(self.client_input, self.client_service.search(ClientSearchQuery()).items, lambda value: value.name)
            except Exception:
                pass

    def _load_equipment(self) -> None:
        self.equipment_input.clear()
        identifier = self.client_input.currentData()
        if not self.equipment_service or not identifier:
            return
        try:
            items = self.equipment_service.search(EquipmentSearchQuery(client_id=identifier)).items
            populate_combo(self.equipment_input, items, lambda value: " — ".join(filter(None, (value.equipment_type, value.brand, value.model, value.serial_number))))
        except Exception:
            pass

    def refresh(self) -> None:
        self.orders_table.setRowCount(0)
        self._orders.clear()
        orders = ()
        if self.service:
            try:
                orders = self.service.search(WorkOrderSearchQuery(self.search_input.text().strip() or None, self.status_filter.currentData())).items
            except Exception:
                pass
        for order in orders:
            short_id = str(order.id)[:8]
            self._orders[short_id] = order
            _table(self.orders_table, (short_id, _status_text(order.status), order.reported_issue, _money(order.total)))
        closed = {WorkOrderStatus.DELIVERED, WorkOrderStatus.REJECTED, WorkOrderStatus.CANCELLED}
        self.summary_cards["total"].set_value(str(len(orders)), "resultado dos filtros")
        self.summary_cards["open"].set_value(str(sum(order.status not in closed for order in orders)), "ordens ativas")
        self.summary_cards["attention"].set_value(str(sum(order.status is WorkOrderStatus.QUOTE_SENT for order in orders)), "orçamentos enviados")
        self._show_selected()

    def _selected_order(self):
        rows = self.orders_table.selectionModel().selectedRows()
        return self._orders.get(self.orders_table.item(rows[0].row(), 0).text()) if rows else None

    def _show_selected(self) -> None:
        self.items_table.setRowCount(0)
        order = self._selected_order()
        if not order:
            self.detail_panel.hide()
            self.empty_state.show()
            return
        self.empty_state.hide()
        self.detail_panel.show()
        self.detail_order_label.setText(f"OS {str(order.id)[:8]} · {order.reported_issue}")
        self.detail_status_label.setText(_status_text(order.status))
        for item in order.items:
            _table(self.items_table, (item.description, item.quantity, _money(item.unit_price), _money(item.amount)))

    def _open(self) -> None:
        if not self.service:
            return
        try:
            if self.client_input.currentData() is None or self.equipment_input.currentData() is None:
                raise ValueError("Selecione o cliente e o equipamento")
            checklist = tuple(value.strip() for value in self.checklist_input.text().split(",") if value.strip())
            self.service.open(OpenWorkOrderCommand(self.client_input.currentData(), self.equipment_input.currentData(), self.issue_input.text(), priority=self.priority_input.currentData(), origin=self.origin_input.text(), checklist=checklist))
            self.operation_tabs.setCurrentIndex(0)
            self.refresh()
        except (DomainError, ValueError) as error:
            QMessageBox.warning(self, "Não foi possível abrir a ordem", str(error))

    def _add_item(self) -> None:
        order = self._selected_order()
        if not self.service or not order:
            return
        try:
            self.service.add_item(AddWorkOrderItemCommand(order.id, self.item_description.text(), Decimal(self.item_quantity.text()), Decimal(self.item_price.text())))
            self.refresh()
        except (DomainError, ValueError, InvalidOperation) as error:
            QMessageBox.warning(self, "Não foi possível adicionar o item", str(error))

    def _transition(self, status: WorkOrderStatus) -> None:
        order = self._selected_order()
        if not self.service or not order:
            return
        try:
            self.service.transition(WorkOrderStatusCommand(order.id, status))
            self.refresh()
        except (DomainError, ValueError) as error:
            QMessageBox.warning(self, "Não foi possível alterar a ordem", str(error))

    def _update_details(self) -> None:
        order = self._selected_order()
        if not self.service or not order:
            return
        try:
            checklist = tuple(value.strip() for value in self.checklist_input.text().split(",") if value.strip())
            self.service.update_details(UpdateWorkOrderDetailsCommand(order.id, priority=self.priority_input.currentData(), origin=self.origin_input.text(), checklist=checklist, observations=self.observations_input.text() or None))
            for value, method in ((self.photo_input.text(), self.service.add_photo), (self.attachment_input.text(), self.service.add_attachment), (self.report_input.text(), self.service.set_report)):
                if value:
                    method(WorkOrderEvidenceCommand(order.id, value))
            self.refresh()
        except (DomainError, ValueError) as error:
            QMessageBox.warning(self, "Não foi possível salvar os detalhes", str(error))


class SalesPage(QWidget):
    def __init__(self, service=None, client_service=None, inventory_service=None):
        super().__init__()
        self.service = service
        self.client_service = client_service
        self.inventory_service = inventory_service
        self.sale = None
        self._parts: dict[str, object] = {}
        self.client_input = SearchableComboBox()
        self.product_input = SearchableComboBox()
        self.product_search_input = QLineEdit()
        self.search_input = self.product_search_input
        self.product_search_input.setPlaceholderText("Leia ou digite código de barras, SKU ou descrição")
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Descrição do item")
        self.quantity_input = QLineEdit("1")
        self.price_input = QLineEdit("0")
        self.discount_input = QLineEdit("0")
        self.received_input = QLineEdit("0")
        self.seller_input = QLineEdit()
        self.seller_input.setPlaceholderText("Vendedor")
        self.quote_input = QLineEdit()
        self.quote_input.setPlaceholderText("Orçamento / OS")
        self.client_input.setMaximumWidth(220)
        self.seller_input.setMaximumWidth(120)
        self.quote_input.setMaximumWidth(120)
        self.payment_method = QComboBox()
        for method in PaymentMethod:
            self.payment_method.addItem(method.value.replace("_", " ").title(), method)

        self.items_table = QTableWidget(0, 5)
        self.items_table.setHorizontalHeaderLabels(["Produto", "Qtd.", "Preço", "Desconto", "Total"])
        self.items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.total_label = QLabel("Total\nR$ 0,00")
        self.total_label.setObjectName("salesTotal")
        self.change_label = QLabel("Troco: R$ 0,00")
        self.change_label.setObjectName("salesChange")
        self.status = QLabel("Nenhuma venda aberta")
        self.status.setObjectName("statusPill")
        self.create_button = QPushButton("F2  Nova venda")
        self.add_button = QPushButton("F4  Adicionar")
        self.pay_button = QPushButton("F8  Registrar pagamento")
        self.complete_button = QPushButton("F10  Concluir venda")
        self.complete_button.setObjectName("primaryAction")

        self.sale_header = QFrame()
        self.sale_header.setObjectName("saleHeader")
        header = QHBoxLayout(self.sale_header)
        header.setContentsMargins(14, 10, 14, 10)
        header.addWidget(self.status)
        header.addStretch()
        header.addWidget(QLabel("Cliente"))
        header.addWidget(self.client_input, 2)
        header.addWidget(self.seller_input)
        header.addWidget(self.quote_input)
        header.addWidget(self.create_button)

        cart_panel, cart = _panel()
        product_row = QGridLayout()
        product_row.addWidget(QLabel("Busca rápida (F3)"), 0, 0)
        product_row.addWidget(QLabel("Produto"), 0, 1, 1, 3)
        product_row.addWidget(self.product_search_input, 1, 0)
        product_row.addWidget(self.product_input, 1, 1, 1, 3)
        for column, (label, control) in enumerate(
            (("Qtd.", self.quantity_input), ("Preço", self.price_input), ("Desconto", self.discount_input))
        ):
            product_row.addWidget(QLabel(label), 2, column)
            product_row.addWidget(control, 3, column)
        product_row.addWidget(self.add_button, 3, 3)
        cart.addLayout(product_row)
        cart.addWidget(self.description_input)
        cart.addWidget(_section("Itens da venda"))
        self.cart_empty_state = EmptyState("Carrinho vazio", "Busque ou leia o código de barras para adicionar o primeiro item.")
        cart.addWidget(self.cart_empty_state)
        cart.addWidget(self.items_table, 1)

        self.checkout_panel, checkout = _panel("checkoutPanel")
        self.checkout_panel.setMinimumWidth(230)
        checkout.addWidget(_section("Fechamento"))
        checkout.addWidget(self.total_label)
        checkout.addWidget(QLabel("Valor recebido"))
        checkout.addWidget(self.received_input)
        checkout.addWidget(QLabel("Forma de pagamento"))
        checkout.addWidget(self.payment_method)
        checkout.addWidget(self.change_label)
        checkout.addStretch()
        checkout.addWidget(self.pay_button)
        checkout.addWidget(self.complete_button)
        workspace = QHBoxLayout()
        workspace.addWidget(cart_panel, 3)
        workspace.addWidget(self.checkout_panel, 1)

        self.page_shell = PageShell("Vendas / PDV", "Venda rápida com carrinho e pagamento no mesmo espaço")
        self.page_shell.body.addWidget(self.sale_header)
        self.page_shell.body.addLayout(workspace, 1)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.addWidget(self.page_shell)

        self.shortcuts = {
            "new": QShortcut(QKeySequence("F2"), self, activated=self._create),
            "search": QShortcut(QKeySequence("F3"), self, activated=self.product_search_input.setFocus),
            "add": QShortcut(QKeySequence("F4"), self, activated=self._add),
            "pay": QShortcut(QKeySequence("F8"), self, activated=self._pay),
            "complete": QShortcut(QKeySequence("F10"), self, activated=self._complete),
        }
        self.create_button.clicked.connect(self._create)
        self.add_button.clicked.connect(self._add)
        self.pay_button.clicked.connect(self._pay)
        self.complete_button.clicked.connect(self._complete)
        self.product_input.currentIndexChanged.connect(self._product_selected)
        self.product_search_input.textChanged.connect(self._load_products)
        self.discount_input.textChanged.connect(self._update_totals)
        self.received_input.textChanged.connect(self._update_totals)
        self._load_data()
        self._render_items()

    def _load_data(self) -> None:
        if self.client_service:
            try:
                populate_combo(self.client_input, self.client_service.search(ClientSearchQuery()).items, lambda value: value.name)
            except Exception:
                pass
        if self.inventory_service:
            self._load_products()

    def _load_products(self) -> None:
        if not self.inventory_service:
            return
        try:
            result = self.inventory_service.search(PartSearchQuery(self.product_search_input.text().strip() or None, page_size=100))
            self._parts = {str(part.id): part for part in result.items}
            populate_combo(self.product_input, result.items, lambda part: f"{part.name} — {part.sku or part.barcode or 'sem código'}")
        except Exception:
            pass

    def _product_selected(self) -> None:
        part = self._parts.get(str(self.product_input.currentData()))
        if part:
            self.description_input.setText(part.name)
            self.price_input.setText(str(part.price))

    def _create(self) -> None:
        if not self.service:
            return
        try:
            self.sale = self.service.create(CreateSaleCommand(self.client_input.currentData()))
            self.status.setText("Venda aberta")
            self._render_items()
            self.product_search_input.setFocus()
        except (DomainError, ValueError) as error:
            QMessageBox.warning(self, "Não foi possível abrir a venda", str(error))

    def _add(self) -> None:
        if not self.service or not self.sale:
            return
        try:
            self.sale = self.service.add_item(AddSaleItemCommand(self.sale.id, self.description_input.text(), Decimal(self.quantity_input.text()), Decimal(self.price_input.text()), self.product_input.currentData(), Decimal(self.discount_input.text() or "0")))
            self._render_items()
            self.product_search_input.clear()
            self.product_search_input.setFocus()
        except (DomainError, ValueError, InvalidOperation) as error:
            QMessageBox.warning(self, "Não foi possível adicionar o item", str(error))

    def _render_items(self) -> None:
        self.items_table.setRowCount(0)
        items = self.sale.items if self.sale else ()
        for item in items:
            discount = getattr(item, "discount", None)
            _table(self.items_table, (item.description, item.quantity, _money(item.unit_price), _money(discount) if discount is not None else "—", _money(item.amount)))
        self.cart_empty_state.setVisible(not bool(items))
        self.items_table.setVisible(bool(items))
        self._update_totals()

    def _update_totals(self) -> None:
        total = self.sale.total if self.sale else Decimal("0")
        try:
            received = Decimal(self.received_input.text() or "0")
        except InvalidOperation:
            received = Decimal("0")
        self.total_label.setText(f"Total\n{_money(total)}")
        self.change_label.setText(f"Troco: {_money(max(Decimal('0'), received - total))}")

    def _complete(self) -> None:
        if not self.service or not self.sale:
            return
        try:
            self.sale = self.service.complete(self.sale.id)
            self.status.setText("Venda concluída")
            self._render_items()
        except (DomainError, ValueError) as error:
            QMessageBox.warning(self, "Não foi possível concluir a venda", str(error))

    def _pay(self) -> None:
        if not self.service or not self.sale:
            return
        try:
            payment = self.service.record_payment(RecordPaymentCommand(self.sale.id, Decimal(self.received_input.text()), self.payment_method.currentData()))
            self.status.setText(f"Pagamento registrado: {_money(payment.amount)}")
        except (DomainError, ValueError, InvalidOperation) as error:
            QMessageBox.warning(self, "Não foi possível registrar o pagamento", str(error))


class InventoryPage(QWidget):
    def __init__(self, service=None):
        super().__init__()
        self.service = service
        self._parts: dict[str, object] = {}
        self._balances: dict[str, tuple[Decimal, Decimal]] = {}
        self.name_input = QLineEdit()
        self.category_input = QLineEdit()
        self.unit_input = QLineEdit("un")
        self.sku_input = QLineEdit()
        self.cost_input = QLineEdit("0")
        self.price_input = QLineEdit("0")
        self.minimum_stock_input = QLineEdit("0")
        self.quantity_input = QLineEdit("1")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por nome, categoria ou SKU")
        self.category_filter = QComboBox()
        self.category_filter.addItem("Todas as categorias", None)
        self.stock_filter = QComboBox()
        self.stock_filter.addItem("Todas as situações", None)
        self.stock_filter.addItem("Abaixo do mínimo", "low")
        self.stock_filter.addItem("Estoque normal", "normal")
        self.parts_table = QTableWidget(0, 6)
        self.parts_table.setHorizontalHeaderLabels(["Peça", "Categoria", "SKU", "Saldo", "Disponível", "Situação"])
        self.parts_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.parts_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.parts_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.movement_type = QComboBox()
        for label, kind in (("Entrada", InventoryMovementType.ENTRY), ("Saída", InventoryMovementType.EXIT), ("Ajuste +", InventoryMovementType.ADJUSTMENT_IN), ("Ajuste -", InventoryMovementType.ADJUSTMENT_OUT)):
            self.movement_type.addItem(label, kind)
        self.balance_label = QLabel("Saldo físico: —  ·  Disponível: —")
        self.selected_part_label = QLabel("Nenhuma peça selecionada")
        self.selected_part_label.setObjectName("detailTitle")
        self.create_button = QPushButton("Cadastrar peça")
        self.create_button.setObjectName("primaryAction")
        self.move_button = QPushButton("Registrar movimentação")
        self.move_button.setObjectName("primaryAction")
        self.refresh_button = QPushButton("Atualizar")
        self.metric_cards = {
            "items": DashboardMetricCard("Itens exibidos", "0", "catálogo filtrado"),
            "low_stock": DashboardMetricCard("Estoque baixo", "0", "requer reposição", "warning"),
            "physical": DashboardMetricCard("Saldo físico", "0", "unidades exibidas", "success"),
        }
        metrics = QHBoxLayout()
        for card in self.metric_cards.values():
            metrics.addWidget(card)
        filters = FilterBar()
        filters.layout.addWidget(self.search_input, 2)
        filters.layout.addWidget(self.category_filter)
        filters.layout.addWidget(self.stock_filter)
        filters.layout.addWidget(self.refresh_button)
        table_panel, table_layout = _panel()
        table_layout.addWidget(_section("Saldo por item"))
        table_layout.addWidget(self.parts_table, 1)
        movement_panel, movement = _panel()
        movement.addWidget(_section("Movimentação"))
        self.movement_empty_state = EmptyState("Selecione uma peça", "Saldo e controles de movimentação aparecerão aqui.")
        self.movement_controls = QFrame()
        controls = QVBoxLayout(self.movement_controls)
        controls.setContentsMargins(0, 0, 0, 0)
        controls.addWidget(self.selected_part_label)
        controls.addWidget(self.balance_label)
        controls.addWidget(QLabel("Tipo de movimento"))
        controls.addWidget(self.movement_type)
        controls.addWidget(QLabel("Quantidade"))
        controls.addWidget(self.quantity_input)
        controls.addStretch()
        controls.addWidget(self.move_button)
        movement.addWidget(self.movement_empty_state)
        movement.addWidget(self.movement_controls, 1)
        self.movement_controls.hide()
        self.workspace_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.workspace_splitter.addWidget(table_panel)
        self.workspace_splitter.addWidget(movement_panel)
        self.workspace_splitter.setSizes([760, 300])

        new_part = QWidget()
        grid = QGridLayout(new_part)
        fields = (("Nome", self.name_input), ("Categoria", self.category_input), ("Unidade", self.unit_input), ("SKU", self.sku_input), ("Custo", self.cost_input), ("Preço", self.price_input), ("Estoque mínimo", self.minimum_stock_input))
        for index, (label, field) in enumerate(fields):
            column, row = index % 4, (index // 4) * 2
            grid.addWidget(QLabel(label), row, column)
            grid.addWidget(field, row + 1, column)
        grid.addWidget(self.create_button, 3, 3)
        operation = QWidget()
        operation_layout = QVBoxLayout(operation)
        operation_layout.setContentsMargins(0, 8, 0, 0)
        operation_layout.addWidget(self.workspace_splitter)
        self.operation_tabs = QTabWidget()
        self.operation_tabs.addTab(operation, "Saldos e movimentações")
        self.operation_tabs.addTab(new_part, "Nova peça")
        self.page_shell = PageShell("Estoque e peças", "Indicadores, alertas e movimentação no mesmo painel")
        self.page_shell.body.addLayout(metrics)
        self.page_shell.body.addWidget(filters)
        self.page_shell.body.addWidget(self.operation_tabs, 1)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.addWidget(self.page_shell)

        self.parts_table.itemSelectionChanged.connect(self._selected_changed)
        self.search_input.textChanged.connect(self.refresh)
        self.category_filter.currentIndexChanged.connect(self.refresh)
        self.stock_filter.currentIndexChanged.connect(self.refresh)
        self.create_button.clicked.connect(self._create)
        self.move_button.clicked.connect(self._movement)
        self.refresh_button.clicked.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        self.parts_table.setRowCount(0)
        self._parts.clear()
        self._balances.clear()
        parts = ()
        if self.service:
            try:
                parts = self.service.search(PartSearchQuery(self.search_input.text().strip() or None, page_size=100)).items
            except Exception:
                pass
        categories = sorted({part.category for part in parts if part.category})
        selected_category = self.category_filter.currentData()
        self.category_filter.blockSignals(True)
        self.category_filter.clear()
        self.category_filter.addItem("Todas as categorias", None)
        for category in categories:
            self.category_filter.addItem(category, category)
        index = self.category_filter.findData(selected_category)
        self.category_filter.setCurrentIndex(max(0, index))
        self.category_filter.blockSignals(False)
        category_filter = self.category_filter.currentData()
        situation_filter = self.stock_filter.currentData()
        physical_total, low_count, visible = Decimal("0"), 0, 0
        for part in parts:
            try:
                physical, available = self.service.balance(part.id)
            except Exception:
                physical, available = Decimal("0"), Decimal("0")
            is_low = physical <= part.minimum_stock
            if category_filter and part.category != category_filter:
                continue
            if situation_filter == "low" and not is_low:
                continue
            if situation_filter == "normal" and is_low:
                continue
            identifier = str(part.id)
            self._parts[identifier] = part
            self._balances[identifier] = (physical, available)
            visible += 1
            physical_total += physical
            low_count += int(is_low)
            _table(self.parts_table, (part.name, part.category, part.sku or "—", physical, available, "Abaixo do mínimo" if is_low else "Normal"))
        self.metric_cards["items"].set_value(str(visible), "catálogo filtrado")
        self.metric_cards["low_stock"].set_value(str(low_count), "requer reposição")
        self.metric_cards["physical"].set_value(str(physical_total), "unidades exibidas")
        self._selected_changed()

    def _selected_id(self) -> str | None:
        rows = self.parts_table.selectionModel().selectedRows()
        return tuple(self._parts)[rows[0].row()] if rows else None

    def _selected_changed(self) -> None:
        identifier = self._selected_id()
        if not identifier:
            self.movement_controls.hide()
            self.movement_empty_state.show()
            return
        part = self._parts[identifier]
        physical, available = self._balances[identifier]
        self.movement_empty_state.hide()
        self.movement_controls.show()
        self.selected_part_label.setText(f"{part.name} · {part.sku or 'sem SKU'}")
        self.balance_label.setText(f"Saldo físico: {physical}  ·  Disponível: {available}")

    def _create(self) -> None:
        if not self.service:
            return
        try:
            self.service.create_part(CreatePartCommand(self.name_input.text(), self.category_input.text(), self.unit_input.text(), self.sku_input.text() or None, Decimal(self.cost_input.text() or "0"), Decimal(self.price_input.text() or "0"), Decimal(self.minimum_stock_input.text() or "0")))
            self.operation_tabs.setCurrentIndex(0)
            self.refresh()
        except (DomainError, ValueError, InvalidOperation) as error:
            QMessageBox.warning(self, "Não foi possível cadastrar a peça", str(error))

    def _movement(self) -> None:
        identifier = self._selected_id()
        if not self.service or identifier is None:
            return
        try:
            self.service.record_movement(RecordInventoryMovementCommand(self._parts[identifier].id, self.movement_type.currentData(), Decimal(self.quantity_input.text())))
            self.refresh()
        except (DomainError, ValueError, InvalidOperation) as error:
            QMessageBox.warning(self, "Não foi possível movimentar o estoque", str(error))
