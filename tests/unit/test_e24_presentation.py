from __future__ import annotations

import os
from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from assistencia_manager.application.services.report_service import ReportResult
from assistencia_manager.domain.entities.access import UserRole
from assistencia_manager.presentation.pages.e24_pages import AccessAuditPage, ReportsPage


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_reports_workspace_persists_filters_populates_indicators_and_supports_sorting():
    _app()
    result = ReportResult(
        "finance",
        ("id", "description", "amount", "status"),
        (
            {"id": "1", "description": "Internet", "amount": Decimal("100"), "status": "open"},
            {"id": "2", "description": "Energia", "amount": Decimal("250"), "status": "paid"},
        ),
    )

    class Service:
        def __init__(self):
            self.calls = []

        def generate(self, kind, filters=None):
            self.calls.append((kind, filters))
            return result

        def export_csv(self, report, destination):
            return destination

        def export_pdf(self, report, destination):
            return destination

    service = Service()
    page = ReportsPage(service)
    page.search_input.setText("energia")
    page.status_filter.setCurrentText("Em aberto")
    page.refresh()

    assert page.results_table.rowCount() == 2
    assert page.results_table.isSortingEnabled()
    assert page.page_size.currentText() == "10"
    assert page.page_label.text() == "Página 1 de 1"
    assert page.metric_cards["records"].value_label.text() == "2"
    assert page.metric_cards["total"].value_label.text() == "R$ 350,00"
    assert service.calls[-1][1].search == "energia"
    assert service.calls[-1][1].status == "open"
    page.refresh()
    assert page.search_input.text() == "energia"
    page.close()


def test_access_workspace_edits_role_permissions_and_filters_masked_audit_history():
    _app()
    user = SimpleNamespace(id="u1", username="operator", display_name="Operador", role=UserRole.OPERATOR, active=True, permissions=frozenset())
    audit = SimpleNamespace(
        id="a1", user_id="u1", action="login", module="auth", entity_type=None,
        entity_id=None, details="senha=segredo telefone=11999999999",
        created_at=datetime.now(timezone.utc),
    )

    class Access:
        def __init__(self): self.updated = None
        def list_users(self): return (user,)
        def set_permissions(self, user_id, permissions): self.updated = (user_id, permissions); return user

    class Audit:
        def list(self, **kwargs): return (audit,)

    access = Access()
    page = AccessAuditPage(access, Audit())
    assert page.role_filter.count() > 1
    assert page.create_button.text() == "Criar usuário"
    assert page.action_filter is not None
    assert page.audit_table.rowCount() == 1
    assert "segredo" not in page.audit_table.item(0, 4).text()
    assert "11999999999" not in page.audit_table.item(0, 4).text()
    page.user_table.selectRow(0)
    page.permission_checks["reports:export"].setChecked(True)
    page.save_permissions()
    assert access.updated[0] == "u1"
    assert any(permission.key == "reports:export" for permission in access.updated[1])
    page.close()
