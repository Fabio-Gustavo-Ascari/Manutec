from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from assistencia_manager.bootstrap import initialize_database
from assistencia_manager.application.services.client_service import ClientService
from assistencia_manager.application.services.equipment_service import EquipmentService
from assistencia_manager.application.services.work_order_service import WorkOrderService
from assistencia_manager.application.services.inventory_service import InventoryService
from assistencia_manager.application.services.sales_service import SalesService
from assistencia_manager.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from assistencia_manager.infrastructure.database.session import create_session_factory
from assistencia_manager.infrastructure.database.repositories.app_metadata import SqlAlchemyAppMetadataRepository
from assistencia_manager.application.services.company_settings_service import CompanySettingsService
from assistencia_manager.application.services.dashboard_service import DashboardService
from assistencia_manager.application.services.report_service import ReportService
from assistencia_manager.application.services.catalog_service import CatalogService
from assistencia_manager.application.services.procurement_service import ProcurementService
from assistencia_manager.application.services.finance_service import FinanceService
from assistencia_manager.application.services.fiscal_service import FiscalService
from assistencia_manager.application.services.access_service import AccessService
from assistencia_manager.application.services.audit_service import AuditService
from assistencia_manager.infrastructure.fiscal_adapters import fiscal_provider_factory
from assistencia_manager.presentation.main_window import MainWindow


def run(argv: list[str] | None = None) -> int:
    application = QApplication(argv or sys.argv)
    application.setApplicationName("Manutec")
    application.setOrganizationName("Manutec")
    engine = initialize_database()
    unit_of_work_factory = lambda: SqlAlchemyUnitOfWork(engine)
    metadata_factory = lambda: SqlAlchemyAppMetadataRepository(create_session_factory(engine)())
    audit_service = AuditService(unit_of_work_factory)
    access_service = AccessService(unit_of_work_factory, audit_service)
    window = MainWindow(
        ClientService(unit_of_work_factory),
        EquipmentService(unit_of_work_factory),
        WorkOrderService(unit_of_work_factory),
        InventoryService(unit_of_work_factory),
        SalesService(unit_of_work_factory),
        DashboardService(unit_of_work_factory),
        ReportService(unit_of_work_factory),
        CompanySettingsService(metadata_factory),
        CatalogService(unit_of_work_factory),
        ProcurementService(unit_of_work_factory),
        FinanceService(unit_of_work_factory),
        FiscalService(metadata_factory, fiscal_provider_factory),
        access_service,
        audit_service,
    )
    window.show()
    return application.exec()
