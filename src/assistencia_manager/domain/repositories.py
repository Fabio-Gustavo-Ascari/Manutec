from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, TypeVar

from assistencia_manager.domain.entities.client import Client
from assistencia_manager.domain.entities.equipment import Equipment
from assistencia_manager.domain.entities.work_order import WorkOrder
from assistencia_manager.domain.entities.inventory import InventoryMovement, Part, PartReservation
from assistencia_manager.domain.entities.sales import CashRegister, Payment, Sale
from assistencia_manager.domain.entities.finance import Commission, FinancialEntry, RecurringExpense
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


class PartRepository(Repository[Part], Protocol):
    def search(self, term: str | None, active_only: bool, offset: int, limit: int) -> Sequence[Part]: ...
    def count(self, term: str | None, active_only: bool) -> int: ...
    def exists_by_sku(self, sku: str) -> bool: ...


class InventoryMovementRepository(Protocol):
    def add(self, movement: InventoryMovement) -> None: ...
    def list_for_part(self, part_id: EntityId) -> Sequence[InventoryMovement]: ...
    def list(self) -> Sequence[InventoryMovement]: ...


class PartReservationRepository(Protocol):
    def add(self, reservation: PartReservation) -> None: ...
    def get(self, identifier: EntityId) -> PartReservation | None: ...
    def list_for_part(self, part_id: EntityId, active_only: bool = False) -> Sequence[PartReservation]: ...
    def list_for_work_order(self, work_order_id: EntityId, active_only: bool = False) -> Sequence[PartReservation]: ...


class SaleRepository(Repository[Sale], Protocol):
    def list_for_work_order(self, work_order_id: EntityId) -> Sequence[Sale]: ...


class PaymentRepository(Repository[Payment], Protocol):
    def list_for_sale(self, sale_id: EntityId) -> Sequence[Payment]: ...


class CashRegisterRepository(Repository[CashRegister], Protocol):
    def current_open(self) -> CashRegister | None: ...


class FinancialEntryRepository(Repository[FinancialEntry], Protocol):
    def list_by_period(self, start, end) -> Sequence[FinancialEntry]: ...


class RecurringExpenseRepository(Repository[RecurringExpense], Protocol):
    pass


class CommissionRepository(Repository[Commission], Protocol):
    pass

