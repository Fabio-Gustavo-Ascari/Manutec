"""Implementações de repositórios do banco local."""

from assistencia_manager.infrastructure.database.repositories.client import (
    SqlAlchemyClientRepository,
)
from assistencia_manager.infrastructure.database.repositories.equipment import (
    SqlAlchemyEquipmentRepository,
)
from assistencia_manager.infrastructure.database.repositories.work_order import (
    SqlAlchemyWorkOrderRepository,
)
from assistencia_manager.infrastructure.database.repositories.inventory import (
    SqlAlchemyInventoryMovementRepository, SqlAlchemyPartRepository,
    SqlAlchemyPartReservationRepository,
)
from assistencia_manager.infrastructure.database.repositories.sales import (
    SqlAlchemyCashRegisterRepository, SqlAlchemyPaymentRepository, SqlAlchemySaleRepository,
)
from assistencia_manager.infrastructure.database.repositories.app_metadata import SqlAlchemyAppMetadataRepository
from assistencia_manager.infrastructure.database.repositories.catalog import SqlAlchemyCatalogRepository, SqlAlchemyServiceRepository, SqlAlchemyServicePackageRepository, SqlAlchemyWarrantyRuleRepository
from assistencia_manager.infrastructure.database.repositories.procurement import SqlAlchemyPurchaseOrderRepository
from assistencia_manager.infrastructure.database.repositories.finance import SqlAlchemyFinancialEntryRepository, SqlAlchemyRecurringExpenseRepository, SqlAlchemyCommissionRepository
from assistencia_manager.infrastructure.database.repositories.access import SqlAlchemyUserRepository, SqlAlchemyAuditRepository

__all__ = [
    "SqlAlchemyClientRepository", "SqlAlchemyEquipmentRepository", "SqlAlchemyWorkOrderRepository",
    "SqlAlchemyPartRepository", "SqlAlchemyInventoryMovementRepository",
    "SqlAlchemyPartReservationRepository",
    "SqlAlchemySaleRepository", "SqlAlchemyPaymentRepository", "SqlAlchemyCashRegisterRepository",
    "SqlAlchemyAppMetadataRepository",
    "SqlAlchemyCatalogRepository", "SqlAlchemyServiceRepository", "SqlAlchemyServicePackageRepository", "SqlAlchemyWarrantyRuleRepository",
    "SqlAlchemyPurchaseOrderRepository", "SqlAlchemyFinancialEntryRepository", "SqlAlchemyRecurringExpenseRepository", "SqlAlchemyCommissionRepository", "SqlAlchemyUserRepository", "SqlAlchemyAuditRepository",
]
