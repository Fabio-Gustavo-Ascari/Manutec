from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from assistencia_manager.bootstrap import initialize_database
from assistencia_manager.application.services.client_service import ClientService
from assistencia_manager.application.services.equipment_service import EquipmentService
from assistencia_manager.application.services.work_order_service import WorkOrderService
from assistencia_manager.application.services.inventory_service import InventoryService
from assistencia_manager.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from assistencia_manager.presentation.main_window import MainWindow


def run(argv: list[str] | None = None) -> int:
    application = QApplication(argv or sys.argv)
    application.setApplicationName("Manutec")
    application.setOrganizationName("Manutec")
    engine = initialize_database()
    unit_of_work_factory = lambda: SqlAlchemyUnitOfWork(engine)
    window = MainWindow(
        ClientService(unit_of_work_factory),
        EquipmentService(unit_of_work_factory),
        WorkOrderService(unit_of_work_factory),
        InventoryService(unit_of_work_factory),
    )
    window.show()
    return application.exec()
