from datetime import date
from decimal import Decimal

from assistencia_manager.application.dto.finance import CreateFinancialEntryCommand
from assistencia_manager.application.services.finance_service import FinanceService
from assistencia_manager.bootstrap import initialize_database
from assistencia_manager.domain.entities.finance import FinancialEntryType
from assistencia_manager.infrastructure.config.paths import AppPaths
from assistencia_manager.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


def test_financial_entry_round_trip_and_cash_flow(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    engine = initialize_database(AppPaths.default())
    make_uow = lambda: SqlAlchemyUnitOfWork(engine)
    service = FinanceService(make_uow)
    entry = service.create_entry(CreateFinancialEntryCommand(
        FinancialEntryType.RECEIVABLE, "OS 10", Decimal("300"), date(2026, 10, 13), source_type="work_order",
    ))
    service.settle(entry.id, paid_date=date(2026, 10, 13))
    with SqlAlchemyUnitOfWork(engine) as uow:
        loaded = uow.financial_entries.get(entry.id)
        assert loaded.remaining_amount == Decimal("0.00")
    flow = service.cash_flow(date(2026, 10, 1), date(2026, 10, 31))
    assert flow.inflow == Decimal("300.00")
    assert flow.balance == Decimal("300.00")
    engine.dispose()
