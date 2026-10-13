from __future__ import annotations

from typing import Protocol, Self

from assistencia_manager.domain.repositories import ClientRepository, EquipmentRepository


class UnitOfWork(Protocol):
    """Porta transacional usada pela aplicação, independente do banco."""

    clients: ClientRepository
    equipment: EquipmentRepository

    def __enter__(self) -> Self: ...

    def __exit__(self, exc_type, exc_value, traceback) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...

