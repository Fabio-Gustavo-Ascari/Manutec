from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from assistencia_manager.application.dto.procurement import CreatePurchaseOrderCommand, ReceivePurchaseOrderCommand, StockCountCommand
from assistencia_manager.domain.entities.inventory import InventoryMovement, InventoryMovementType, StockLedger
from assistencia_manager.domain.entities.procurement import PurchaseOrder, PurchaseOrderLine
from assistencia_manager.domain.exceptions import DomainValidationError, EntityNotFoundError
from assistencia_manager.domain.unit_of_work import UnitOfWork


@dataclass(frozen=True, slots=True)
class ReorderSuggestion:
    part_id: object
    current_quantity: Decimal
    suggested_quantity: Decimal


class ProcurementService:
    def __init__(self, unit_of_work_factory: Callable[[], UnitOfWork]) -> None:
        self._unit_of_work_factory = unit_of_work_factory

    def create_order(self, command: CreatePurchaseOrderCommand) -> PurchaseOrder:
        with self._unit_of_work_factory() as uow:
            lines = []
            for part_id, quantity, unit_cost in command.lines:
                self._part(uow, part_id)
                lines.append(PurchaseOrderLine(part_id, quantity, unit_cost))
            order = PurchaseOrder.create(supplier_id=command.supplier_id, lines=tuple(lines), due_date=command.due_date, notes=command.notes)
            uow.purchase_orders.add(order)
            return order

    def receive(self, command: ReceivePurchaseOrderCommand) -> PurchaseOrder:
        with self._unit_of_work_factory() as uow:
            order = uow.purchase_orders.get(command.purchase_order_id)
            if order is None:
                raise EntityNotFoundError("Pedido de compra não encontrado")
            receipts = {line.part_id: line.quantity for line in command.lines}
            for line in command.lines:
                part = self._part(uow, line.part_id)
                part.ensure_active()
                if line.quantity <= 0:
                    raise DomainValidationError("Quantidade recebida deve ser maior que zero")
            before = {line.part_id: line.received_quantity for line in order.lines}
            order.receive(receipts)
            for line in order.lines:
                quantity = line.received_quantity - before[line.part_id]
                if quantity:
                    self._record_entry(uow, line.part_id, quantity, order.id, line.unit_cost)
            uow.purchase_orders.add(order)
            return order

    def count(self, command: StockCountCommand) -> InventoryMovement:
        with self._unit_of_work_factory() as uow:
            part = self._part(uow, command.part_id)
            if command.counted_quantity < 0:
                raise DomainValidationError("Contagem não pode ser negativa")
            movements = tuple(uow.inventory_movements.list_for_part(part.id))
            current = StockLedger(movements).physical_balance(part.id)
            delta = Decimal(str(command.counted_quantity)) - current
            if not delta:
                raise DomainValidationError("Contagem não alterou o saldo")
            kind = InventoryMovementType.ADJUSTMENT_IN if delta > 0 else InventoryMovementType.ADJUSTMENT_OUT
            movement = InventoryMovement(part.id, kind, abs(delta), note=command.note)
            uow.inventory_movements.add(movement)
            return movement

    def reorder_suggestions(self) -> tuple[ReorderSuggestion, ...]:
        with self._unit_of_work_factory() as uow:
            suggestions = []
            for part in uow.parts.list():
                current = StockLedger(tuple(uow.inventory_movements.list_for_part(part.id))).physical_balance(part.id)
                if current <= part.minimum_stock:
                    target = getattr(part, "maximum_stock", Decimal("0")) or part.minimum_stock
                    suggestions.append(ReorderSuggestion(part.id, current, max(Decimal("0"), target - current)))
            return tuple(suggestions)

    @staticmethod
    def _part(uow: UnitOfWork, part_id):
        part = uow.parts.get(part_id)
        if part is None:
            raise EntityNotFoundError("Peça não encontrada")
        return part

    @staticmethod
    def _record_entry(uow, part_id, quantity, order_id, unit_cost):
        part = ProcurementService._part(uow, part_id)
        existing = StockLedger(tuple(uow.inventory_movements.list_for_part(part_id))).physical_balance(part_id)
        if existing + quantity:
            part.cost = ((part.cost * existing + unit_cost * quantity) / (existing + quantity)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            uow.parts.add(part)
        uow.inventory_movements.add(InventoryMovement(part_id, InventoryMovementType.ENTRY, quantity, reference_id=order_id, note="recebimento de compra"))
