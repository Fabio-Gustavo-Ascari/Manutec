from __future__ import annotations

import os
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from assistencia_manager.domain.entities.finance import FinancialEntryStatus, FinancialEntryType
from assistencia_manager.domain.entities.fiscal import FiscalEnvironment
from assistencia_manager.presentation.pages.e23_pages import CompanySettingsPage, FinancePage, FiscalPage


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_finance_workspace_shows_period_summary_and_settles_selected_entry():
    _app()
    entry = SimpleNamespace(
        id="entry-1", description="Internet", entry_type=FinancialEntryType.PAYABLE,
        due_date=date.today(), status=FinancialEntryStatus.OPEN, amount=Decimal("100"),
        remaining_amount=Decimal("100"), paid_amount=Decimal("0"),
    )
    settled = []

    class Service:
        def list_entries(self, **kwargs): return (entry,)
        def settle(self, identifier): settled.append(identifier); entry.status = FinancialEntryStatus.PAID; entry.remaining_amount = Decimal("0")

    page = FinancePage(Service())
    assert set(page.metric_cards) == {"inflow", "outflow", "balance", "open"}
    assert page.entries_table.rowCount() == 1
    page.entries_table.selectRow(0); page.settle_button.click()
    assert settled == ["entry-1"]
    assert "sucesso" in page.message_label.text()
    page.close()


def test_fiscal_workspace_exposes_environment_status_and_diagnostics():
    _app()
    calls = []

    class Service:
        def get_configuration(self): return None
        def configure(self, command):
            calls.append(command)
            return SimpleNamespace(environment=FiscalEnvironment.PRODUCTION, provider="simulated")

    page = FiscalPage(Service())
    page.document.setText("12345678000190"); page.environment.setCurrentText("production"); page.findChildren(__import__("PySide6.QtWidgets", fromlist=["QPushButton"]).QPushButton)[0].click()
    assert calls and calls[0].environment is FiscalEnvironment.PRODUCTION
    assert "salva" in page.message_label.text()
    page.close()


def test_settings_workspace_groups_fields_and_reports_save_feedback():
    _app()
    values = {field: "" for field in ("name", "document", "address", "phone", "email")}

    class Service:
        def get(self): return values
        def update(self, new_values): values.update(new_values); return values

    page = CompanySettingsPage(Service())
    assert len(page.findChildren(__import__("PySide6.QtWidgets", fromlist=["QGroupBox"]).QGroupBox)) == 2
    page.inputs["name"].setText("Manutec"); page.save()
    assert "sucesso" in page.message_label.text()
    page.close()
