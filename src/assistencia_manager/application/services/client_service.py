from __future__ import annotations

from collections.abc import Callable
from collections.abc import Sequence

from assistencia_manager.application.dto.client import (
    ClientSearchQuery,
    CreateClientCommand,
    UpdateClientCommand,
)
from assistencia_manager.application.dto.pagination import Page
from assistencia_manager.domain.entities.client import Client
from assistencia_manager.domain.exceptions import EntityNotFoundError
from assistencia_manager.domain.identifiers import EntityId
from assistencia_manager.domain.unit_of_work import UnitOfWork


class ClientService:
    def __init__(self, unit_of_work_factory: Callable[[], UnitOfWork]) -> None:
        self._unit_of_work_factory = unit_of_work_factory

    def create(self, command: CreateClientCommand) -> Client:
        with self._unit_of_work_factory() as unit_of_work:
            client = Client(
                name=command.name,
                contacts=command.contacts,
                document=command.document,
                address=command.address,
                notes=command.notes,
            )
            unit_of_work.clients.add(client)
            return client

    def update(self, command: UpdateClientCommand) -> Client:
        with self._unit_of_work_factory() as unit_of_work:
            client = unit_of_work.clients.get(command.identifier)
            if client is None:
                raise EntityNotFoundError(f"Cliente {command.identifier} não encontrado")
            client.update(
                name=command.name,
                contacts=command.contacts,
                document=command.document,
                address=command.address,
                notes=command.notes,
            )
            unit_of_work.clients.add(client)
            return client

    def get(self, identifier: EntityId) -> Client:
        with self._unit_of_work_factory() as unit_of_work:
            client = unit_of_work.clients.get(identifier)
            if client is None:
                raise EntityNotFoundError(f"Cliente {identifier} não encontrado")
            return client

    def list(self) -> Sequence[Client]:
        with self._unit_of_work_factory() as unit_of_work:
            return tuple(unit_of_work.clients.list())

    def deactivate(self, identifier: EntityId) -> Client:
        with self._unit_of_work_factory() as unit_of_work:
            client = unit_of_work.clients.get(identifier)
            if client is None:
                raise EntityNotFoundError(f"Cliente {identifier} não encontrado")
            client.deactivate()
            unit_of_work.clients.add(client)
            return client

    def search(self, query: ClientSearchQuery) -> Page[Client]:
        with self._unit_of_work_factory() as unit_of_work:
            offset = (query.page - 1) * query.page_size
            items = unit_of_work.clients.search(query.search, offset, query.page_size)
            return Page(
                items=tuple(items),
                page=query.page,
                page_size=query.page_size,
                total_items=unit_of_work.clients.count(query.search),
            )
