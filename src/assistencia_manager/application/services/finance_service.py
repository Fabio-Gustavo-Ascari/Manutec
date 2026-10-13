from __future__ import annotations

from calendar import monthrange
from collections.abc import Callable
from datetime import date
from decimal import Decimal

from assistencia_manager.application.dto.finance import (
    CreateFinancialEntryCommand, CreateRecurringExpenseCommand, RecordCommissionCommand,
)
from assistencia_manager.domain.entities.finance import (
    CashFlowSummary, Commission, FinancialEntry, FinancialEntryStatus,
    FinancialEntryType, RecurringExpense,
)
from assistencia_manager.domain.exceptions import DomainValidationError, EntityNotFoundError


class FinanceService:
    def __init__(self, unit_of_work_factory: Callable[[], object]) -> None:
        self._unit_of_work_factory = unit_of_work_factory

    def create_entry(self, command: CreateFinancialEntryCommand) -> FinancialEntry:
        with self._unit_of_work_factory() as uow:
            entry = FinancialEntry(command.entry_type, command.description, command.amount, command.due_date, command.category, command.cost_center, command.source_type, command.source_id)
            uow.financial_entries.add(entry)
            return entry

    def settle(self, identifier, amount=None, paid_date=None) -> FinancialEntry:
        with self._unit_of_work_factory() as uow:
            entry = uow.financial_entries.get(identifier)
            if entry is None:
                raise EntityNotFoundError("Lançamento financeiro não encontrado")
            if entry.status is FinancialEntryStatus.PAID:
                return entry
            entry.settle(amount, paid_date)
            uow.financial_entries.add(entry)
            return entry

    def create_recurring(self, command: CreateRecurringExpenseCommand) -> RecurringExpense:
        with self._unit_of_work_factory() as uow:
            expense = RecurringExpense(command.description, command.amount, command.due_day, command.category, command.cost_center)
            uow.recurring_expenses.add(expense)
            return expense

    def generate_recurring(self, identifier, *, year: int, month: int) -> FinancialEntry:
        with self._unit_of_work_factory() as uow:
            expense = uow.recurring_expenses.get(identifier)
            if expense is None:
                raise EntityNotFoundError("Despesa recorrente não encontrada")
            due = date(year, month, min(expense.due_day, monthrange(year, month)[1]))
            duplicate = next((item for item in uow.financial_entries.list() if item.source_type == "recurring" and item.source_id == expense.id and item.due_date == due), None)
            if duplicate:
                raise DomainValidationError("Despesa recorrente já gerada para o período")
            entry = FinancialEntry(FinancialEntryType.PAYABLE, expense.description, expense.amount, due, expense.category, expense.cost_center, "recurring", expense.id)
            uow.financial_entries.add(entry)
            return entry

    def record_commission(self, command: RecordCommissionCommand) -> Commission:
        with self._unit_of_work_factory() as uow:
            commission = Commission(command.seller_id, command.sale_id, command.base_amount, command.percentage)
            uow.commissions.add(commission)
            return commission

    def cash_flow(self, start: date, end: date) -> CashFlowSummary:
        if end < start:
            raise DomainValidationError("Período inválido")
        with self._unit_of_work_factory() as uow:
            entries = tuple(uow.financial_entries.list())
            period = [item for item in entries if start <= (item.paid_date or item.due_date) <= end]
            inflow = sum((item.paid_amount for item in period if item.entry_type is FinancialEntryType.RECEIVABLE), Decimal("0.00"))
            outflow = sum((item.paid_amount for item in period if item.entry_type is FinancialEntryType.PAYABLE), Decimal("0.00"))
            open_payables = sum((item.remaining_amount for item in entries if item.entry_type is FinancialEntryType.PAYABLE and item.status in {FinancialEntryStatus.OPEN, FinancialEntryStatus.PARTIAL}), Decimal("0.00"))
            open_receivables = sum((item.remaining_amount for item in entries if item.entry_type is FinancialEntryType.RECEIVABLE and item.status in {FinancialEntryStatus.OPEN, FinancialEntryStatus.PARTIAL}), Decimal("0.00"))
            return CashFlowSummary(start, end, inflow, outflow, inflow - outflow, open_payables, open_receivables)

    def list_entries(self, *, start: date | None = None, end: date | None = None,
                     entry_type: FinancialEntryType | None = None) -> tuple[FinancialEntry, ...]:
        """Consulta lançamentos para a apresentação sem expor a unidade de trabalho."""
        with self._unit_of_work_factory() as uow:
            entries = tuple(uow.financial_entries.list())
        if start is not None: entries = tuple(item for item in entries if item.due_date >= start)
        if end is not None: entries = tuple(item for item in entries if item.due_date <= end)
        if entry_type is not None: entries = tuple(item for item in entries if item.entry_type is entry_type)
        return entries

    def close_period(self, start: date, end: date) -> CashFlowSummary:
        """Returns the immutable financial closing snapshot for a period."""
        return self.cash_flow(start, end)
