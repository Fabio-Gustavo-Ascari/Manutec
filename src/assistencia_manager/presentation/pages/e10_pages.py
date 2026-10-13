from __future__ import annotations

from decimal import Decimal, InvalidOperation

from PySide6.QtWidgets import QComboBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from assistencia_manager.application.dto.client import ClientSearchQuery
from assistencia_manager.application.dto.equipment import EquipmentSearchQuery
from assistencia_manager.application.dto.inventory import CreatePartCommand, PartSearchQuery, RecordInventoryMovementCommand
from assistencia_manager.application.dto.sales import AddSaleItemCommand, CreateSaleCommand, RecordPaymentCommand
from assistencia_manager.application.dto.work_order import AddWorkOrderItemCommand, OpenWorkOrderCommand, WorkOrderSearchQuery, WorkOrderStatusCommand
from assistencia_manager.domain.entities.inventory import InventoryMovementType
from assistencia_manager.domain.entities.sales import PaymentMethod
from assistencia_manager.domain.entities.work_order import WorkOrderStatus
from assistencia_manager.domain.exceptions import DomainError
from assistencia_manager.presentation.shell import PageShell, SearchableComboBox, populate_combo


def _table(table, values):
    row = table.rowCount(); table.insertRow(row)
    for col, value in enumerate(values): table.setItem(row, col, QTableWidgetItem(str(value)))


class WorkOrdersPage(QWidget):
    def __init__(self, service=None, client_service=None, equipment_service=None):
        super().__init__(); self.service, self.client_service, self.equipment_service = service, client_service, equipment_service; self._orders = {}
        self.search_input = QLineEdit(); self.search_input.setPlaceholderText("Buscar por defeito, cliente ou número")
        self.status_filter = QComboBox(); self.status_filter.addItem("Todos", None); [self.status_filter.addItem(s.value.replace("_", " ").title(), s) for s in WorkOrderStatus]
        self.client_label = QLabel("Cliente"); self.client_input = SearchableComboBox(); self.equipment_input = SearchableComboBox(); self.issue_input = QLineEdit(); self.issue_input.setPlaceholderText("Descreva o defeito relatado")
        self.item_description = QLineEdit(); self.item_quantity = QLineEdit("1"); self.item_price = QLineEdit("0")
        self.items_table = QTableWidget(0, 4); self.items_table.setHorizontalHeaderLabels(["Item", "Qtd.", "Unitário", "Total"])
        self.orders_table = QTableWidget(0, 4); self.orders_table.setHorizontalHeaderLabels(["OS", "Status", "Defeito", "Total"]); self.orders_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows); self.orders_table.itemSelectionChanged.connect(self._show_selected)
        self.client_input.currentIndexChanged.connect(self._load_equipment); self.search_input.textChanged.connect(self.refresh); self.status_filter.currentIndexChanged.connect(self.refresh)
        open_button = QPushButton("Abrir ordem"); open_button.setObjectName("primaryAction"); open_button.clicked.connect(self._open); add_button = QPushButton("Adicionar item"); add_button.clicked.connect(self._add_item); refresh_button = QPushButton("Atualizar"); refresh_button.clicked.connect(self.refresh); approve_button = QPushButton("Aprovar"); approve_button.clicked.connect(lambda: self._transition(WorkOrderStatus.APPROVED)); cancel_button = QPushButton("Cancelar"); cancel_button.clicked.connect(lambda: self._transition(WorkOrderStatus.CANCELLED))
        form = QFormLayout(); form.addRow(self.client_label, self.client_input); form.addRow("Equipamento", self.equipment_input); form.addRow("Defeito relatado", self.issue_input)
        item_form = QHBoxLayout(); item_form.addWidget(self.item_description, 2); item_form.addWidget(self.item_quantity); item_form.addWidget(self.item_price); item_form.addWidget(add_button)
        actions = QHBoxLayout(); [actions.addWidget(x) for x in (open_button, refresh_button, approve_button, cancel_button)]
        filters = QHBoxLayout(); filters.addWidget(self.search_input, 2); filters.addWidget(self.status_filter)
        shell = PageShell("Ordens de serviço", "Abertura, orçamento e acompanhamento do atendimento"); shell.body.addLayout(form); shell.body.addLayout(filters); shell.body.addLayout(actions); shell.body.addWidget(self.orders_table, 2); shell.body.addWidget(QLabel("Itens da ordem selecionada")); shell.body.addLayout(item_form); shell.body.addWidget(self.items_table)
        layout = QVBoxLayout(self); layout.setContentsMargins(18, 18, 18, 18); layout.addWidget(shell); self._load_clients(); self.refresh()

    def _load_clients(self):
        if not self.client_service: return
        try: populate_combo(self.client_input, self.client_service.search(ClientSearchQuery()).items, lambda x: x.name)
        except Exception: pass

    def _load_equipment(self):
        self.equipment_input.clear(); identifier = self.client_input.currentData()
        if not self.equipment_service or not identifier: return
        try: populate_combo(self.equipment_input, self.equipment_service.search(EquipmentSearchQuery(client_id=identifier)).items, lambda x: " — ".join(filter(None, (x.equipment_type, x.brand, x.model, x.serial_number))))
        except Exception: pass

    def refresh(self):
        self.orders_table.setRowCount(0); self._orders.clear()
        if not self.service: return
        try: page = self.service.search(WorkOrderSearchQuery(self.search_input.text().strip() or None, self.status_filter.currentData()))
        except Exception: return
        for order in page.items: self._orders[str(order.id)[:8]] = order; _table(self.orders_table, (str(order.id)[:8], order.status.value.replace("_", " ").title(), order.reported_issue, order.total))

    def _selected_order(self):
        rows = self.orders_table.selectionModel().selectedRows(); return self._orders.get(self.orders_table.item(rows[0].row(), 0).text()) if rows else None

    def _show_selected(self):
        self.items_table.setRowCount(0); order = self._selected_order()
        if order:
            for item in order.items: _table(self.items_table, (item.description, item.quantity, item.unit_price, item.amount))

    def _open(self):
        if not self.service: return
        try:
            if self.client_input.currentData() is None or self.equipment_input.currentData() is None: raise ValueError("Selecione o cliente e o equipamento")
            self.service.open(OpenWorkOrderCommand(self.client_input.currentData(), self.equipment_input.currentData(), self.issue_input.text())); self.refresh()
        except (DomainError, ValueError) as error: QMessageBox.warning(self, "Não foi possível abrir a ordem", str(error))

    def _add_item(self):
        order = self._selected_order()
        if not self.service or not order: return
        try: self.service.add_item(AddWorkOrderItemCommand(order.id, self.item_description.text(), Decimal(self.item_quantity.text()), Decimal(self.item_price.text()))); self.refresh()
        except (DomainError, ValueError) as error: QMessageBox.warning(self, "Não foi possível adicionar o item", str(error))

    def _transition(self, status):
        order = self._selected_order()
        if not self.service or not order: return
        try: self.service.transition(WorkOrderStatusCommand(order.id, status)); self.refresh()
        except (DomainError, ValueError) as error: QMessageBox.warning(self, "Não foi possível alterar a ordem", str(error))


class SalesPage(QWidget):
    def __init__(self, service=None, client_service=None, inventory_service=None):
        super().__init__(); self.service, self.client_service, self.inventory_service, self.sale = service, client_service, inventory_service, None; self._parts = {}
        self.client_input = SearchableComboBox(); self.product_input = SearchableComboBox(); self.description_input = QLineEdit(); self.quantity_input = QLineEdit("1"); self.price_input = QLineEdit("0"); self.discount_input = QLineEdit("0"); self.received_input = QLineEdit("0")
        self.payment_method = QComboBox(); [self.payment_method.addItem(m.value.replace("_", " ").title(), m) for m in PaymentMethod]
        self.items_table = QTableWidget(0, 5); self.items_table.setHorizontalHeaderLabels(["Produto", "Qtd.", "Preço", "Desconto", "Total"]); self.total_label = QLabel("Total: R$ 0,00"); self.change_label = QLabel("Troco: R$ 0,00"); self.status = QLabel("Nenhuma venda aberta")
        self.product_input.currentIndexChanged.connect(self._product_selected); self.discount_input.textChanged.connect(self._update_totals); self.received_input.textChanged.connect(self._update_totals)
        create = QPushButton("Nova venda"); create.clicked.connect(self._create); add = QPushButton("Adicionar item"); add.clicked.connect(self._add); complete = QPushButton("Concluir venda"); complete.setObjectName("primaryAction"); complete.clicked.connect(self._complete); pay = QPushButton("Registrar pagamento"); pay.clicked.connect(self._pay)
        form = QFormLayout(); form.addRow("Cliente", self.client_input); form.addRow("Produto/peça", self.product_input); form.addRow("Descrição", self.description_input); form.addRow("Quantidade", self.quantity_input); form.addRow("Preço unitário", self.price_input); form.addRow("Desconto", self.discount_input); form.addRow("Recebido", self.received_input); form.addRow("Forma de pagamento", self.payment_method)
        actions = QHBoxLayout(); [actions.addWidget(x) for x in (create, add, complete, pay)]; summary = QHBoxLayout(); summary.addWidget(self.total_label); summary.addWidget(self.change_label); summary.addStretch()
        shell = PageShell("Vendas e caixa", "Carrinho, desconto, recebimento e troco"); shell.body.addLayout(form); shell.body.addLayout(actions); shell.body.addWidget(self.items_table, 1); shell.body.addLayout(summary); shell.body.addWidget(self.status); layout = QVBoxLayout(self); layout.setContentsMargins(18, 18, 18, 18); layout.addWidget(shell); self._load_data()

    def _load_data(self):
        if self.client_service:
            try: populate_combo(self.client_input, self.client_service.search(ClientSearchQuery()).items, lambda x: x.name)
            except Exception: pass
        if self.inventory_service:
            try:
                result = self.inventory_service.search(PartSearchQuery(page_size=100)); self._parts = {str(x.id): x for x in result.items}; populate_combo(self.product_input, result.items, lambda x: f"{x.name} — {x.sku or 'sem SKU'}")
            except Exception: pass

    def _product_selected(self):
        part = self._parts.get(str(self.product_input.currentData()))
        if part: self.description_input.setText(part.name); self.price_input.setText(str(part.price))

    def _create(self):
        if not self.service: return
        try: self.sale = self.service.create(CreateSaleCommand(self.client_input.currentData())); self.status.setText("Venda aberta")
        except (DomainError, ValueError) as error: QMessageBox.warning(self, "Não foi possível abrir a venda", str(error))

    def _add(self):
        if not self.service or not self.sale: return
        try: self.sale = self.service.add_item(AddSaleItemCommand(self.sale.id, self.description_input.text(), Decimal(self.quantity_input.text()), Decimal(self.price_input.text()), self.product_input.currentData())); self._render_items()
        except (DomainError, ValueError, InvalidOperation) as error: QMessageBox.warning(self, "Não foi possível adicionar o item", str(error))

    def _render_items(self):
        self.items_table.setRowCount(0)
        if self.sale:
            for item in self.sale.items: _table(self.items_table, (item.description, item.quantity, item.unit_price, "—", item.amount))
        self._update_totals()

    def _update_totals(self):
        total = self.sale.total if self.sale else Decimal("0")
        try: discount, received = Decimal(self.discount_input.text() or "0"), Decimal(self.received_input.text() or "0")
        except InvalidOperation: discount, received = Decimal("0"), Decimal("0")
        total = max(Decimal("0"), total - discount); self.total_label.setText(f"Total: R$ {total:.2f}"); self.change_label.setText(f"Troco: R$ {max(Decimal('0'), received-total):.2f}")

    def _complete(self):
        if not self.service or not self.sale: return
        try: self.sale = self.service.complete(self.sale.id); self.status.setText("Venda concluída"); self._render_items()
        except (DomainError, ValueError) as error: QMessageBox.warning(self, "Não foi possível concluir a venda", str(error))

    def _pay(self):
        if not self.service or not self.sale: return
        try: payment = self.service.record_payment(RecordPaymentCommand(self.sale.id, Decimal(self.received_input.text()), self.payment_method.currentData())); self.status.setText(f"Pagamento registrado: {payment.amount}")
        except (DomainError, ValueError, InvalidOperation) as error: QMessageBox.warning(self, "Não foi possível registrar o pagamento", str(error))


class InventoryPage(QWidget):
    def __init__(self, service=None):
        super().__init__(); self.service = service; self._parts = {}
        self.name_input = QLineEdit(); self.category_input = QLineEdit(); self.unit_input = QLineEdit("un"); self.sku_input = QLineEdit(); self.cost_input = QLineEdit("0"); self.price_input = QLineEdit("0"); self.minimum_stock_input = QLineEdit("0"); self.quantity_input = QLineEdit("1"); self.search_input = QLineEdit(); self.search_input.setPlaceholderText("Buscar por nome, categoria ou SKU"); self.search_input.textChanged.connect(self.refresh)
        self.parts_table = QTableWidget(0, 6); self.parts_table.setHorizontalHeaderLabels(["Peça", "Categoria", "SKU", "Saldo", "Disponível", "Situação"]); self.parts_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows); self.parts_table.itemSelectionChanged.connect(self._selected_changed)
        self.movement_type = QComboBox(); [(self.movement_type.addItem(label, kind)) for label, kind in (("Entrada", InventoryMovementType.ENTRY), ("Saída", InventoryMovementType.EXIT), ("Ajuste +", InventoryMovementType.ADJUSTMENT_IN), ("Ajuste -", InventoryMovementType.ADJUSTMENT_OUT))]; self.balance_label = QLabel("Selecione uma peça para ver o saldo")
        create = QPushButton("Cadastrar peça"); create.setObjectName("primaryAction"); create.clicked.connect(self._create); move = QPushButton("Registrar movimentação"); move.clicked.connect(self._movement); refresh = QPushButton("Atualizar"); refresh.clicked.connect(self.refresh)
        form = QFormLayout(); [form.addRow(label, field) for label, field in (("Nome", self.name_input), ("Categoria", self.category_input), ("Unidade", self.unit_input), ("SKU", self.sku_input), ("Custo", self.cost_input), ("Preço", self.price_input), ("Estoque mínimo", self.minimum_stock_input))]
        movement = QHBoxLayout(); movement.addWidget(self.movement_type); movement.addWidget(self.quantity_input); movement.addWidget(move); movement.addWidget(self.balance_label, 1); actions = QHBoxLayout(); actions.addWidget(create); actions.addWidget(refresh); actions.addStretch()
        shell = PageShell("Estoque e peças", "Catálogo, saldos, alertas e movimentações auditáveis"); shell.body.addWidget(self.search_input); shell.body.addLayout(form); shell.body.addLayout(actions); shell.body.addWidget(self.parts_table, 1); shell.body.addLayout(movement); layout = QVBoxLayout(self); layout.setContentsMargins(18, 18, 18, 18); layout.addWidget(shell); self.refresh()

    def refresh(self):
        self.parts_table.setRowCount(0); self._parts.clear()
        if not self.service: return
        try: page = self.service.search(PartSearchQuery(self.search_input.text().strip() or None))
        except Exception: return
        for part in page.items:
            self._parts[str(part.id)] = part
            try: physical, available = self.service.balance(part.id)
            except Exception: physical, available = Decimal("0"), Decimal("0")
            _table(self.parts_table, (part.name, part.category, part.sku or "—", physical, available, "Abaixo do mínimo" if physical <= part.minimum_stock else "Normal"))

    def _selected_id(self):
        rows = self.parts_table.selectionModel().selectedRows(); return tuple(self._parts)[rows[0].row()] if rows else None

    def _selected_changed(self):
        identifier = self._selected_id()
        if identifier and self.service:
            try: self.balance_label.setText(f"Saldo: {self.service.balance(self._parts[identifier].id)[0]}")
            except Exception: pass

    def _create(self):
        if not self.service: return
        try: self.service.create_part(CreatePartCommand(self.name_input.text(), self.category_input.text(), self.unit_input.text(), self.sku_input.text() or None, Decimal(self.cost_input.text() or "0"), Decimal(self.price_input.text() or "0"), Decimal(self.minimum_stock_input.text() or "0"))); self.refresh()
        except (DomainError, ValueError, InvalidOperation) as error: QMessageBox.warning(self, "Não foi possível cadastrar a peça", str(error))

    def _movement(self):
        identifier = self._selected_id()
        if not self.service or identifier is None: return
        try: self.service.record_movement(RecordInventoryMovementCommand(self._parts[identifier].id, self.movement_type.currentData(), Decimal(self.quantity_input.text()))); self.refresh()
        except (DomainError, ValueError, InvalidOperation) as error: QMessageBox.warning(self, "Não foi possível movimentar o estoque", str(error))
