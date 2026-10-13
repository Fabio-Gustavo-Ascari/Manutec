from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
import sqlite3

from assistencia_manager.application.services.backup_service import BackupService
from assistencia_manager.application.services.company_settings_service import CompanySettingsService
from assistencia_manager.application.services.dashboard_service import DashboardService
from assistencia_manager.application.services.report_service import ReportService
from assistencia_manager.domain.entities.inventory import InventoryMovement, InventoryMovementType, Part
from assistencia_manager.domain.entities.sales import Payment, PaymentMethod, Sale
from assistencia_manager.domain.entities.work_order import WorkOrder, WorkOrderStatus
from assistencia_manager.domain.identifiers import EntityId


class FakeRepository:
    def __init__(self, values=()):
        self.values = list(values)

    def list(self):
        return tuple(self.values)


class FakeUow:
    def __init__(self, orders=(), parts=(), movements=(), sales=(), payments=()):
        self.work_orders = FakeRepository(orders)
        self.parts = FakeRepository(parts)
        self.inventory_movements = FakeRepository(movements)
        self.sales = FakeRepository(sales)
        self.payments = FakeRepository(payments)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return None


def test_dashboard_counts_status_deadlines_revenue_and_low_stock():
    now = datetime.now(timezone.utc)
    client_id, equipment_id = EntityId.new(), EntityId.new()
    late = WorkOrder.open(client_id=client_id, equipment_id=equipment_id, reported_issue="A")
    late.due_at = now - timedelta(days=1)
    late.status = WorkOrderStatus.IN_PROGRESS
    part = Part.create(name="Tela", category="Peças", unit="un", cost=10, price=20, minimum_stock=2)
    sale = Sale.create()
    sale.add_item(description="Serviço", quantity=1, unit_price=100)
    sale.complete()
    payment = Payment.record(sale_id=sale.id, amount=75, method=PaymentMethod.PIX)
    sale.add_payment(payment)
    movement = InventoryMovement(part.id, InventoryMovementType.ENTRY, 1)

    result = DashboardService(lambda: FakeUow([late], [part], [movement], [sale], [payment])).snapshot()

    assert result.orders_by_status[WorkOrderStatus.IN_PROGRESS.value] == 1
    assert result.overdue_orders == 1
    assert result.received_revenue == Decimal("75.00")
    assert result.low_stock_parts == 1


def test_company_settings_are_persisted_and_report_is_filterable_and_exportable(tmp_path):
    from assistencia_manager.infrastructure.database.engine import create_engine
    from assistencia_manager.infrastructure.database.session import create_session_factory
    from assistencia_manager.infrastructure.database.repositories.app_metadata import SqlAlchemyAppMetadataRepository
    from assistencia_manager.bootstrap import initialize_database
    from assistencia_manager.infrastructure.config.paths import AppPaths

    paths = AppPaths(tmp_path, tmp_path / "data", tmp_path / "app.db", tmp_path / "logs", tmp_path / "backups")
    engine = initialize_database(paths)
    factory = create_session_factory(engine)
    service = CompanySettingsService(lambda: SqlAlchemyAppMetadataRepository(factory()))
    service.update({"name": "Oficina Central", "document": "00.000.000/0000-00"})
    assert service.get()["name"] == "Oficina Central"

    report = ReportService(lambda: FakeUow())
    output = report.export_orders_csv([], tmp_path / "reports" / "orders.csv")
    assert output.exists()
    assert "status" in output.read_text(encoding="utf-8")
    engine.dispose()


def test_backup_round_trip_validates_manifest_and_preserves_database(tmp_path):
    database = tmp_path / "data" / "app.db"
    database.parent.mkdir()
    connection = sqlite3.connect(database)
    connection.execute("CREATE TABLE sample (value TEXT)")
    connection.execute("INSERT INTO sample VALUES ('old')")
    connection.commit()
    connection.close()
    service = BackupService(database, tmp_path / "backups", application_version="0.1.0")

    backup = service.create()
    connection = sqlite3.connect(database)
    connection.execute("DELETE FROM sample")
    connection.commit()
    connection.close()
    service.restore(backup)

    connection = sqlite3.connect(database)
    assert connection.execute("SELECT value FROM sample").fetchone()[0] == "old"
    connection.close()
