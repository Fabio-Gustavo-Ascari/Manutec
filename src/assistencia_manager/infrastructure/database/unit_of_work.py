from __future__ import annotations

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from assistencia_manager.infrastructure.database.session import create_session_factory
from assistencia_manager.infrastructure.database.repositories import (
    SqlAlchemyClientRepository,
    SqlAlchemyEquipmentRepository,
    SqlAlchemyWorkOrderRepository,
    SqlAlchemyInventoryMovementRepository, SqlAlchemyPartRepository,
    SqlAlchemyPartReservationRepository,
    SqlAlchemySaleRepository, SqlAlchemyPaymentRepository, SqlAlchemyCashRegisterRepository,
    SqlAlchemyCatalogRepository, SqlAlchemyServiceRepository, SqlAlchemyServicePackageRepository, SqlAlchemyWarrantyRuleRepository,
    SqlAlchemyPurchaseOrderRepository,
)


class SqlAlchemyUnitOfWork:
    """Implementação da unidade de trabalho para o banco local."""

    def __init__(self, engine: Engine) -> None:
        self._session_factory = create_session_factory(engine)
        self.session: Session | None = None
        self.clients: SqlAlchemyClientRepository | None = None
        self.equipment: SqlAlchemyEquipmentRepository | None = None
        self.work_orders: SqlAlchemyWorkOrderRepository | None = None
        self.parts: SqlAlchemyPartRepository | None = None
        self.inventory_movements: SqlAlchemyInventoryMovementRepository | None = None
        self.reservations: SqlAlchemyPartReservationRepository | None = None
        self.sales: SqlAlchemySaleRepository | None = None
        self.payments: SqlAlchemyPaymentRepository | None = None
        self.cash_registers: SqlAlchemyCashRegisterRepository | None = None
        self.catalogs = self.services = self.service_packages = self.warranty_rules = None
        self.purchase_orders = None

    def __enter__(self) -> SqlAlchemyUnitOfWork:
        self.session = self._session_factory()
        self.clients = SqlAlchemyClientRepository(self.session)
        self.equipment = SqlAlchemyEquipmentRepository(self.session)
        self.work_orders = SqlAlchemyWorkOrderRepository(self.session)
        self.parts = SqlAlchemyPartRepository(self.session)
        self.inventory_movements = SqlAlchemyInventoryMovementRepository(self.session)
        self.reservations = SqlAlchemyPartReservationRepository(self.session)
        self.sales = SqlAlchemySaleRepository(self.session)
        self.payments = SqlAlchemyPaymentRepository(self.session)
        self.cash_registers = SqlAlchemyCashRegisterRepository(self.session)
        self.catalogs = SqlAlchemyCatalogRepository(self.session)
        self.services = SqlAlchemyServiceRepository(self.session)
        self.service_packages = SqlAlchemyServicePackageRepository(self.session)
        self.warranty_rules = SqlAlchemyWarrantyRuleRepository(self.session)
        self.purchase_orders = SqlAlchemyPurchaseOrderRepository(self.session)
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        try:
            if exc_type is None:
                self.commit()
            else:
                self.rollback()
        finally:
            if self.session is not None:
                self.session.close()
                self.session = None
                self.clients = None
                self.equipment = None
                self.work_orders = None
                self.parts = None
                self.inventory_movements = None
                self.reservations = None
                self.sales = None
                self.payments = None
                self.cash_registers = None
                self.catalogs = self.services = self.service_packages = self.warranty_rules = None
                self.purchase_orders = None

    def commit(self) -> None:
        if self.session is None:
            raise RuntimeError("Unidade de trabalho não está aberta")
        self.session.commit()

    def rollback(self) -> None:
        if self.session is not None:
            self.session.rollback()

    def flush(self) -> None:
        if self.session is None:
            raise RuntimeError("Unidade de trabalho não está aberta")
        self.session.flush()

