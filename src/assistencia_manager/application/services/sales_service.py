from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal

from assistencia_manager.application.dto.sales import (
    AddSaleItemCommand, CashMovementCommand, CreateSaleCommand, OpenCashCommand,
    RemoveSaleItemCommand, UpdateSaleItemCommand,
    ReceiveWorkOrderCommand, RecordPaymentCommand,
)
from assistencia_manager.domain.entities.inventory import InventoryMovementType, StockLedger
from assistencia_manager.domain.entities.sales import CashRegister, Payment, Sale, SaleStatus
from assistencia_manager.domain.exceptions import DomainValidationError, EntityNotFoundError
from assistencia_manager.domain.unit_of_work import UnitOfWork


class SalesService:
    def __init__(self, unit_of_work_factory: Callable[[], UnitOfWork]) -> None:
        self._unit_of_work_factory = unit_of_work_factory

    def create(self, command: CreateSaleCommand) -> Sale:
        with self._unit_of_work_factory() as uow:
            sale = Sale.create(command.client_id, command.work_order_id, command.seller_id, command.quote_id)
            uow.sales.add(sale)
            return sale

    def add_item(self, command: AddSaleItemCommand) -> Sale:
        with self._unit_of_work_factory() as uow:
            sale = self._sale(uow, command.sale_id)
            sale.add_item(description=command.description, quantity=command.quantity, unit_price=command.unit_price, part_id=command.part_id, discount=command.discount)
            uow.sales.add(sale)
            return sale

    def update_item(self, command: UpdateSaleItemCommand) -> Sale:
        with self._unit_of_work_factory() as uow:
            sale = self._sale(uow, command.sale_id)
            sale.update_item(command.index, quantity=command.quantity, unit_price=command.unit_price, discount=command.discount)
            uow.sales.add(sale)
            return sale

    def remove_item(self, command: RemoveSaleItemCommand) -> Sale:
        with self._unit_of_work_factory() as uow:
            sale = self._sale(uow, command.sale_id)
            sale.remove_item(command.index)
            uow.sales.add(sale)
            return sale

    def complete(self, identifier) -> Sale:
        with self._unit_of_work_factory() as uow:
            sale = self._sale(uow, identifier)
            sale.complete()
            for item in sale.items:
                if item.part_id is None: continue
                ledger = StockLedger(tuple(uow.inventory_movements.list_for_part(item.part_id)))
                movement = ledger.record(part_id=item.part_id, movement_type=InventoryMovementType.EXIT, quantity=item.quantity, reference_id=sale.id, note="Venda")
                uow.inventory_movements.add(movement)
            uow.sales.add(sale)
            return sale

    def cancel(self, identifier) -> Sale:
        with self._unit_of_work_factory() as uow:
            sale = self._sale(uow, identifier)
            was_completed = sale.status is SaleStatus.COMPLETED
            sale.cancel()
            if was_completed:
                for item in sale.items:
                    if item.part_id is not None:
                        uow.inventory_movements.add(StockLedger(tuple(uow.inventory_movements.list_for_part(item.part_id))).record(part_id=item.part_id, movement_type=InventoryMovementType.RETURN, quantity=item.quantity, reference_id=sale.id, note="Estorno da venda"))
                for payment in tuple(sale.payments):
                    if payment.status.value == "paid":
                        payment.reverse()
                        uow.payments.add(payment)
                        register = uow.cash_registers.current_open()
                        if register:
                            register.record(amount=payment.amount, description=f"Cancelamento {sale.id}", movement_type="out")
                            uow.cash_registers.add(register)
            uow.sales.add(sale)
            return sale

    def record_payment(self, command: RecordPaymentCommand) -> Payment:
        with self._unit_of_work_factory() as uow:
            sale = self._sale(uow, command.sale_id)
            if sale.status is not SaleStatus.COMPLETED:
                raise DomainValidationError("Pagamento só pode ser registrado em venda concluída")
            payment = Payment.record(sale_id=sale.id, amount=command.amount, method=command.method, installments=command.installments)
            sale.add_payment(payment)
            uow.payments.add(payment)
            uow.sales.add(sale)
            register = uow.cash_registers.current_open()
            if register:
                register.record(amount=payment.amount, description=f"Venda {sale.id}")
                uow.cash_registers.add(register)
            return payment

    def reverse_payment(self, identifier) -> Payment:
        with self._unit_of_work_factory() as uow:
            payment = uow.payments.get(identifier)
            if payment is None: raise EntityNotFoundError(f"Pagamento {identifier} não encontrado")
            payment.reverse()
            uow.payments.add(payment)
            register = uow.cash_registers.current_open()
            if register:
                register.record(amount=payment.amount, description=f"Estorno {payment.id}", movement_type="out")
                uow.cash_registers.add(register)
            return payment

    def receive_work_order(self, command: ReceiveWorkOrderCommand) -> Payment:
        with self._unit_of_work_factory() as uow:
            order = uow.work_orders.get(command.work_order_id)
            if order is None: raise EntityNotFoundError(f"Ordem {command.work_order_id} não encontrada")
            sale = next(iter(uow.sales.list_for_work_order(order.id)), None)
            if sale is None:
                sale = Sale.create(client_id=order.client_id, work_order_id=order.id)
                sale.add_item(description=f"Ordem de serviço {order.id}", quantity=1, unit_price=order.total)
                sale.complete()
                uow.sales.add(sale)
                uow.flush()
            payment = Payment.record(sale_id=sale.id, amount=command.amount, method=command.method, installments=command.installments)
            sale.add_payment(payment)
            uow.payments.add(payment)
            uow.sales.add(sale)
            return payment

    def open_cash(self, command: OpenCashCommand = OpenCashCommand()) -> CashRegister:
        with self._unit_of_work_factory() as uow:
            if uow.cash_registers.current_open() is not None: raise DomainValidationError("Já existe caixa aberto")
            register = CashRegister.opening(amount=command.amount)
            uow.cash_registers.add(register)
            return register

    def move_cash(self, command: CashMovementCommand) -> CashRegister:
        with self._unit_of_work_factory() as uow:
            register = uow.cash_registers.get(command.cash_register_id)
            if register is None: raise EntityNotFoundError("Caixa não encontrado")
            register.record(amount=command.amount, description=command.description, movement_type=command.movement_type)
            uow.cash_registers.add(register)
            return register

    def close_cash(self, identifier) -> CashRegister:
        with self._unit_of_work_factory() as uow:
            register = uow.cash_registers.get(identifier)
            if register is None: raise EntityNotFoundError("Caixa não encontrado")
            register.close()
            uow.cash_registers.add(register)
            return register

    @staticmethod
    def _sale(uow: UnitOfWork, identifier) -> Sale:
        sale = uow.sales.get(identifier)
        if sale is None: raise EntityNotFoundError(f"Venda {identifier} não encontrada")
        sale.payments = list(uow.payments.list_for_sale(sale.id))
        return sale
