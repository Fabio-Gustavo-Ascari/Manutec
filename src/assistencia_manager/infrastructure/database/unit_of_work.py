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

    def __enter__(self) -> SqlAlchemyUnitOfWork:
        self.session = self._session_factory()
        self.clients = SqlAlchemyClientRepository(self.session)
        self.equipment = SqlAlchemyEquipmentRepository(self.session)
        self.work_orders = SqlAlchemyWorkOrderRepository(self.session)
        self.parts = SqlAlchemyPartRepository(self.session)
        self.inventory_movements = SqlAlchemyInventoryMovementRepository(self.session)
        self.reservations = SqlAlchemyPartReservationRepository(self.session)
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

    def commit(self) -> None:
        if self.session is None:
            raise RuntimeError("Unidade de trabalho não está aberta")
        self.session.commit()

    def rollback(self) -> None:
        if self.session is not None:
            self.session.rollback()

