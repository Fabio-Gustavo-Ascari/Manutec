from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from assistencia_manager.application.services.access_service import AccessService
from assistencia_manager.application.services.audit_service import AuditService
from assistencia_manager.application.services.report_service import ReportFilters, ReportService
from assistencia_manager.domain.entities.access import Permission, UserRole
from assistencia_manager.domain.exceptions import DomainValidationError
from assistencia_manager.domain.identifiers import EntityId


class MemoryUsers:
    def __init__(self): self.values = []
    def add(self, user): self.values.append(user)
    def get(self, identifier): return next((u for u in self.values if u.id == identifier), None)
    def get_by_username(self, username): return next((u for u in self.values if u.username == username), None)
    def list(self): return tuple(self.values)


class MemoryAudit:
    def __init__(self): self.values = []
    def add(self, entry): self.values.append(entry)
    def list(self): return tuple(self.values)
    def get(self, identifier): return next((e for e in self.values if e.id == identifier), None)


class Uow:
    def __init__(self):
        self.users = MemoryUsers()
        self.audit_logs = MemoryAudit()
    def __enter__(self): return self
    def __exit__(self, *args): pass
    def commit(self): pass
    def rollback(self): pass


def test_local_user_authentication_permissions_and_audit():
    uow = Uow()
    access = AccessService(lambda: uow)
    audit = AuditService(lambda: uow)
    credential = "P" * 12
    user = access.create_user("Admin", "admin", credential, UserRole.ADMIN)

    assert access.authenticate("admin", credential).id == user.id
    assert access.can(user, Permission("reports", "export"))
    assert access.can(user, Permission("unknown", "delete"))
    with pytest.raises(DomainValidationError):
        access.authenticate("admin", "X" * 12)
    audit.record(user_id=user.id, action="login_failed", module="auth")
    assert audit.list()[0].action == "login_failed"


def test_reports_filter_and_sanitized_csv(tmp_path: Path):
    class Orders:
        def list(self):
            return (type("Order", (), {
                "id": EntityId.new(), "status": type("Status", (), {"value": "completed"})(),
                "reported_issue": "=HYPERLINK(\"https://evil\")", "total": Decimal("123.45"),
                "technician_id": None, "client_id": EntityId.new(), "due_at": None,
                "delivered_at": None, "warranty_until": None,
            })(),)
    class ReportsUow:
        work_orders = Orders()
        def __enter__(self): return self
        def __exit__(self, *args): pass
    service = ReportService(lambda: ReportsUow())
    result = service.generate("work_orders", ReportFilters(status="completed", client_id="missing"))
    assert result.rows == ()
    result = service.generate("work_orders", ReportFilters(status="completed"))
    target = service.export_csv(result, tmp_path / "report.csv")
    assert "'=HYPERLINK" in target.read_text(encoding="utf-8")

