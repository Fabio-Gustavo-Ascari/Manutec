from __future__ import annotations

from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from assistencia_manager.infrastructure.database.session import create_session_factory
from assistencia_manager.infrastructure.database.repositories import (
    SqlAlchemyClientRepository,
    SqlAlchemyEquipmentRepository,
    SqlAlchemyWorkOrderRepository,
)


class SqlAlchemyUnitOfWork:
    """Implementação da unidade de trabalho para o banco local."""

    def __init__(self, engine: Engine) -> None:
        self._session_factory = create_session_factory(engine)
        self.session: Session | None = None
        self.clients: SqlAlchemyClientRepository | None = None
        self.equipment: SqlAlchemyEquipmentRepository | None = None
        self.work_orders: SqlAlchemyWorkOrderRepository | None = None

    def __enter__(self) -> SqlAlchemyUnitOfWork:
        self.session = self._session_factory()
        self.clients = SqlAlchemyClientRepository(self.session)
        self.equipment = SqlAlchemyEquipmentRepository(self.session)
        self.work_orders = SqlAlchemyWorkOrderRepository(self.session)
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

    def commit(self) -> None:
        if self.session is None:
            raise RuntimeError("Unidade de trabalho não está aberta")
        self.session.commit()

    def rollback(self) -> None:
        if self.session is not None:
            self.session.rollback()

