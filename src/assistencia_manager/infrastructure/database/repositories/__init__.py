"""Implementações de repositórios do banco local."""

from assistencia_manager.infrastructure.database.repositories.client import (
    SqlAlchemyClientRepository,
)
from assistencia_manager.infrastructure.database.repositories.equipment import (
    SqlAlchemyEquipmentRepository,
)

__all__ = ["SqlAlchemyClientRepository", "SqlAlchemyEquipmentRepository"]
