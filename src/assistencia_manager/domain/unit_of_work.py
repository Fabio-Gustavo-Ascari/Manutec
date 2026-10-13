from __future__ import annotations

from typing import Protocol, Self

from assistencia_manager.domain.repositories import (
    ClientRepository, EquipmentRepository, InventoryMovementRepository,
    PartRepository, PartReservationRepository, WorkOrderRepository,
    SaleRepository, PaymentRepository, CashRegisterRepository,
)


class UnitOfWork(Protocol):
    """Porta transacional usada pela aplicação, independente do banco."""

    clients: ClientRepository
    equipment: EquipmentRepository
    work_orders: WorkOrderRepository
    parts: PartRepository
    inventory_movements: InventoryMovementRepository
    reservations: PartReservationRepository
    sales: SaleRepository
    payments: PaymentRepository
    cash_registers: CashRegisterRepository
    catalogs: object
    services: object
    service_packages: object
    warranty_rules: object
    purchase_orders: object

    def __enter__(self) -> Self: ...

    def __exit__(self, exc_type, exc_value, traceback) -> None: ...

    def commit(self) -> None: ...

    def rollback(self) -> None: ...

    def flush(self) -> None: ...

