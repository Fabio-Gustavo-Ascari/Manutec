from datetime import date
from decimal import Decimal

import pytest

from assistencia_manager.application.dto.finance import (
    CreateFinancialEntryCommand,
    CreateRecurringExpenseCommand,
    RecordCommissionCommand,
)
from assistencia_manager.application.services.finance_service import FinanceService
from assistencia_manager.domain.entities.finance import (
    FinancialEntryStatus,
    FinancialEntryType,
)
from assistencia_manager.domain.exceptions import DomainValidationError
from assistencia_manager.domain.identifiers import EntityId


class Repo:
    def __init__(self):
        self.data = {}

    def add(self, entity):
        self.data[entity.id] = entity

    def get(self, identifier):
        return self.data.get(identifier)

    def list(self):
        return tuple(self.data.values())


class Uow:
    def __init__(self):
        self.financial_entries = Repo()
        self.recurring_expenses = Repo()
        self.commissions = Repo()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def test_payable_can_be_created_and_settled_idempotently():
    uow = Uow()
    service = FinanceService(lambda: uow)
    entry = service.create_entry(CreateFinancialEntryCommand(
        entry_type=FinancialEntryType.PAYABLE,
        description="Internet",
        amount=Decimal("150.00"),
        due_date=date(2026, 10, 20),
    ))

    settled = service.settle(entry.id, paid_date=date(2026, 10, 20))
    assert settled.status is FinancialEntryStatus.PAID
    assert settled.remaining_amount == Decimal("0.00")
    assert service.settle(entry.id).status is FinancialEntryStatus.PAID


def test_recurring_expense_generates_entries_for_month_and_rejects_duplicate():
    uow = Uow()
    service = FinanceService(lambda: uow)
    recurring = service.create_recurring(CreateRecurringExpenseCommand(
        description="Aluguel", amount=Decimal("1000"), due_day=10,
    ))

    generated = service.generate_recurring(recurring.id, year=2026, month=10)
    assert generated.entry_type is FinancialEntryType.PAYABLE
    assert generated.due_date == date(2026, 10, 10)
    with pytest.raises(DomainValidationError):
        service.generate_recurring(recurring.id, year=2026, month=10)


def test_commission_is_calculated_from_received_amount():
    uow = Uow()
    service = FinanceService(lambda: uow)
    commission = service.record_commission(RecordCommissionCommand(
        seller_id=EntityId.new(), sale_id=EntityId.new(),
        base_amount=Decimal("250"), percentage=Decimal("5"),
    ))
    assert commission.amount == Decimal("12.50")

