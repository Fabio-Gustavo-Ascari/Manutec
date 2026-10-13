from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from assistencia_manager.domain.entities.base import EntityStatus
from assistencia_manager.domain.entities.client import Client
from assistencia_manager.domain.identifiers import EntityId
from assistencia_manager.infrastructure.database.models.client import ClientModel


class SqlAlchemyClientRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, entity: Client) -> None:
        self._session.merge(
            ClientModel(
                id=str(entity.id),
                status=entity.status.value,
                name=entity.name,
                contacts=list(entity.contacts),
                document=entity.document,
                address=entity.address,
                notes=entity.notes,
            )
        )

    def get(self, identifier: EntityId) -> Client | None:
        model = self._session.get(ClientModel, str(identifier))
        if model is None:
            return None
        return Client(
            id=EntityId.from_str(model.id),
            status=EntityStatus(model.status),
            name=model.name,
            contacts=tuple(model.contacts or ()),
            document=model.document,
            address=model.address,
            notes=model.notes,
        )

    def list(self) -> tuple[Client, ...]:
        return tuple(self._to_entity(model) for model in self._session.scalars(select(ClientModel)))

    def remove(self, identifier: EntityId) -> None:
        model = self._session.get(ClientModel, str(identifier))
        if model is not None:
            self._session.delete(model)

    def exists_by_name(self, name: str) -> bool:
        return self._session.scalar(select(ClientModel.id).where(ClientModel.name == name).limit(1)) is not None

    def search(self, term: str | None, offset: int, limit: int) -> tuple[Client, ...]:
        statement = select(ClientModel)
        if term and term.strip():
            pattern = f"%{term.strip()}%"
            statement = statement.where(
                ClientModel.name.ilike(pattern)
                | ClientModel.document.ilike(pattern)
                | ClientModel.address.ilike(pattern)
            )
        statement = statement.order_by(ClientModel.name).offset(offset).limit(limit)
        return tuple(self._to_entity(model) for model in self._session.scalars(statement))

    def count(self, term: str | None) -> int:
        statement = select(ClientModel.id)
        if term and term.strip():
            pattern = f"%{term.strip()}%"
            statement = statement.where(
                ClientModel.name.ilike(pattern)
                | ClientModel.document.ilike(pattern)
                | ClientModel.address.ilike(pattern)
            )
        return self._session.scalar(select(func.count()).select_from(statement.subquery())) or 0

    @staticmethod
    def _to_entity(model: ClientModel) -> Client:
        return Client(
            id=EntityId.from_str(model.id),
            status=EntityStatus(model.status),
            name=model.name,
            contacts=tuple(model.contacts or ()),
            document=model.document,
            address=model.address,
            notes=model.notes,
        )
