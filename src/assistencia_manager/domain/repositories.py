from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, TypeVar

from assistencia_manager.domain.entities.client import Client
from assistencia_manager.domain.entities.equipment import Equipment
from assistencia_manager.domain.entities.work_order import WorkOrder
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

    def search(self, term: str | None, offset: int, limit: int) -> Sequence[Client]: ...

    def count(self, term: str | None) -> int: ...


class EquipmentRepository(Repository[Equipment], Protocol):
    """Porta de persistência dos equipamentos."""

    def exists_by_serial_number(self, serial_number: str) -> bool: ...

    def search(
        self,
        term: str | None,
        client_id: EntityId | None,
        offset: int,
        limit: int,
    ) -> Sequence[Equipment]: ...

    def count(self, term: str | None, client_id: EntityId | None) -> int: ...


class WorkOrderRepository(Repository[WorkOrder], Protocol):
    def search(
        self, term: str | None, status: str | None, offset: int, limit: int
    ) -> Sequence[WorkOrder]: ...

    def count(self, term: str | None, status: str | None) -> int: ...

