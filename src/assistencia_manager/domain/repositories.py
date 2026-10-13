from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, TypeVar

from assistencia_manager.domain.entities.client import Client
from assistencia_manager.domain.entities.equipment import Equipment
from assistencia_manager.domain.identifiers import EntityId

EntityT = TypeVar("EntityT")


class Repository(Protocol[EntityT]):
    """Porta mínima para persistência de entidades, sem tecnologia acoplada."""

    def add(self, entity: EntityT) -> None: ...

    def get(self, identifier: EntityId) -> EntityT | None: ...

    def list(self) -> Sequence[EntityT]: ...

    def remove(self, identifier: EntityId) -> None: ...


class ClientRepository(Repository[Client], Protocol):
    """Porta de persistência dos clientes."""

    def exists_by_name(self, name: str) -> bool: ...


class EquipmentRepository(Repository[Equipment], Protocol):
    """Porta de persistência dos equipamentos."""

    def exists_by_serial_number(self, serial_number: str) -> bool: ...

