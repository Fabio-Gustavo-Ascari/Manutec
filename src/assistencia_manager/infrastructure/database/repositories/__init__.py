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

__all__ = ["SqlAlchemyClientRepository", "SqlAlchemyEquipmentRepository", "SqlAlchemyWorkOrderRepository"]
