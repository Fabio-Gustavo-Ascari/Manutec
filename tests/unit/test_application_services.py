from __future__ import annotations

from collections.abc import Sequence
from copy import deepcopy

import pytest

from assistencia_manager.domain.entities.client import Client
from assistencia_manager.domain.entities.equipment import Equipment
from assistencia_manager.domain.exceptions import DomainValidationError, EntityNotFoundError
from assistencia_manager.domain.identifiers import EntityId


class InMemoryClientRepository:
    def __init__(self) -> None:
        self.items: dict[EntityId, Client] = {}

    def add(self, entity: Client) -> None:
        self.items[entity.id] = entity

    def get(self, identifier: EntityId) -> Client | None:
        return self.items.get(identifier)

    def list(self) -> Sequence[Client]:
        return tuple(self.items.values())

    def remove(self, identifier: EntityId) -> None:
        self.items.pop(identifier, None)

    def exists_by_name(self, name: str) -> bool:
        return any(client.name == name for client in self.items.values())

    def search(self, term: str | None, offset: int, limit: int) -> Sequence[Client]:
        normalized = (term or "").strip().casefold()
        matches = tuple(
            client
            for client in self.items.values()
            if not normalized or normalized in client.name.casefold()
        )
        return matches[offset : offset + limit]

    def count(self, term: str | None) -> int:
        return len(self.search(term, 0, len(self.items)))


class InMemoryEquipmentRepository:
    def __init__(self) -> None:
        self.items: dict[EntityId, Equipment] = {}

    def add(self, entity: Equipment) -> None:
        self.items[entity.id] = entity

    def get(self, identifier: EntityId) -> Equipment | None:
        return self.items.get(identifier)

    def list(self) -> Sequence[Equipment]:
        return tuple(self.items.values())

    def remove(self, identifier: EntityId) -> None:
        self.items.pop(identifier, None)

    def exists_by_serial_number(self, serial_number: str) -> bool:
        return any(item.serial_number == serial_number for item in self.items.values())

    def search(
        self,
        term: str | None,
        client_id: EntityId | None,
        offset: int,
        limit: int,
    ) -> Sequence[Equipment]:
        normalized = (term or "").strip().casefold()
        matches = tuple(
            equipment
            for equipment in self.items.values()
            if (client_id is None or equipment.client_id == client_id)
            and (
                not normalized
                or normalized in equipment.equipment_type.casefold()
                or normalized in (equipment.brand or "").casefold()
                or normalized in (equipment.model or "").casefold()
                or normalized in (equipment.serial_number or "").casefold()
            )
        )
        return matches[offset : offset + limit]

    def count(self, term: str | None, client_id: EntityId | None) -> int:
        return len(self.search(term, client_id, 0, len(self.items)))


class InMemoryUnitOfWork:
    def __init__(self) -> None:
        self.clients = InMemoryClientRepository()
        self.equipment = InMemoryEquipmentRepository()
        self.commits = 0
        self.rollbacks = 0
        self._snapshot: tuple[dict[EntityId, Client], dict[EntityId, Equipment]] | None = None

    def __enter__(self) -> InMemoryUnitOfWork:
        self._snapshot = (deepcopy(self.clients.items), deepcopy(self.equipment.items))
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if exc_type is None:
            self.commit()
        else:
            self.rollback()

    def commit(self) -> None:
        self.commits += 1

    def rollback(self) -> None:
        self.rollbacks += 1
        if self._snapshot is not None:
            self.clients.items, self.equipment.items = deepcopy(self._snapshot)


@pytest.fixture
def unit_of_work() -> InMemoryUnitOfWork:
    return InMemoryUnitOfWork()


def test_client_service_creates_and_commits_client(unit_of_work: InMemoryUnitOfWork):
    from assistencia_manager.application.dto.client import CreateClientCommand
    from assistencia_manager.application.services.client_service import ClientService

    service = ClientService(lambda: unit_of_work)

    created = service.create(CreateClientCommand(name=" Oficina Central ", contacts=(" 11 9999 ",)))

    assert created.name == "Oficina Central"
    assert created in unit_of_work.clients.list()
    assert unit_of_work.commits == 1


def test_equipment_service_requires_existing_client(unit_of_work: InMemoryUnitOfWork):
    from assistencia_manager.application.dto.equipment import CreateEquipmentCommand
    from assistencia_manager.application.services.equipment_service import EquipmentService

    service = EquipmentService(lambda: unit_of_work)

    with pytest.raises(EntityNotFoundError):
        service.create(
            CreateEquipmentCommand(client_id=EntityId.new(), equipment_type="Notebook")
        )

    assert unit_of_work.equipment.list() == ()
    assert unit_of_work.commits == 0
    assert unit_of_work.rollbacks == 1


def test_client_service_updates_client_preserving_identity(unit_of_work: InMemoryUnitOfWork):
    from assistencia_manager.application.dto.client import CreateClientCommand, UpdateClientCommand
    from assistencia_manager.application.services.client_service import ClientService

    client = Client(name="Antigo")
    unit_of_work.clients.add(client)
    service = ClientService(lambda: unit_of_work)

    updated = service.update(UpdateClientCommand(identifier=client.id, name="Novo"))

    assert updated is client
    assert updated.id == client.id
    assert updated.name == "Novo"


def test_equipment_service_updates_equipment_preserving_identity_and_client(
    unit_of_work: InMemoryUnitOfWork,
):
    from assistencia_manager.application.dto.client import CreateClientCommand
    from assistencia_manager.application.dto.equipment import (
        CreateEquipmentCommand,
        UpdateEquipmentCommand,
    )
    from assistencia_manager.application.services.client_service import ClientService
    from assistencia_manager.application.services.equipment_service import EquipmentService

    client = ClientService(lambda: unit_of_work).create(CreateClientCommand(name="Cliente"))
    equipment = Equipment(client_id=client.id, equipment_type="Notebook")
    unit_of_work.equipment.add(equipment)

    updated = EquipmentService(lambda: unit_of_work).update(
        UpdateEquipmentCommand(identifier=equipment.id, equipment_type="Desktop", model="X")
    )

    assert updated is equipment
    assert updated.id == equipment.id
    assert updated.client_id == client.id
    assert updated.equipment_type == "Desktop"
    assert updated.model == "X"


def test_services_raise_when_entity_to_update_does_not_exist(unit_of_work: InMemoryUnitOfWork):
    from assistencia_manager.application.dto.client import UpdateClientCommand
    from assistencia_manager.application.dto.equipment import UpdateEquipmentCommand
    from assistencia_manager.application.services.client_service import ClientService
    from assistencia_manager.application.services.equipment_service import EquipmentService

    with pytest.raises(EntityNotFoundError):
        ClientService(lambda: unit_of_work).update(
            UpdateClientCommand(identifier=EntityId.new(), name="Novo")
        )
    with pytest.raises(EntityNotFoundError):
        EquipmentService(lambda: unit_of_work).update(
            UpdateEquipmentCommand(identifier=EntityId.new(), equipment_type="Notebook")
        )


def test_invalid_client_update_is_rolled_back(unit_of_work: InMemoryUnitOfWork):
    from assistencia_manager.application.dto.client import UpdateClientCommand
    from assistencia_manager.application.services.client_service import ClientService

    client = Client(name="Antigo")
    unit_of_work.clients.add(client)

    with pytest.raises(DomainValidationError):
        ClientService(lambda: unit_of_work).update(
            UpdateClientCommand(identifier=client.id, name="Novo", contacts=(object(),))
        )

    assert unit_of_work.clients.get(client.id).name == "Antigo"
    assert unit_of_work.rollbacks == 1


def test_client_service_consults_lists_and_inactivates_clients(
    unit_of_work: InMemoryUnitOfWork,
):
    from assistencia_manager.application.dto.client import CreateClientCommand
    from assistencia_manager.application.services.client_service import ClientService

    service = ClientService(lambda: unit_of_work)
    first = service.create(CreateClientCommand(name="Primeiro"))
    second = service.create(CreateClientCommand(name="Segundo"))

    assert service.get(first.id) is first
    assert service.list() == (first, second)

    inactive = service.deactivate(first.id)

    assert inactive is first
    assert inactive.status.value == "inactive"
    assert service.get(first.id) is first


def test_equipment_service_consults_lists_and_inactivates_equipment(
    unit_of_work: InMemoryUnitOfWork,
):
    from assistencia_manager.application.dto.client import CreateClientCommand
    from assistencia_manager.application.dto.equipment import CreateEquipmentCommand
    from assistencia_manager.application.services.client_service import ClientService
    from assistencia_manager.application.services.equipment_service import EquipmentService

    client = ClientService(lambda: unit_of_work).create(CreateClientCommand(name="Cliente"))
    service = EquipmentService(lambda: unit_of_work)
    first = service.create(CreateEquipmentCommand(client_id=client.id, equipment_type="Notebook"))
    second = service.create(CreateEquipmentCommand(client_id=client.id, equipment_type="Desktop"))

    assert service.get(first.id) is first
    assert service.list() == (first, second)

    inactive = service.deactivate(first.id)

    assert inactive is first
    assert inactive.status.value == "inactive"
    assert service.get(first.id) is first


def test_query_and_inactivate_raise_when_entity_does_not_exist(
    unit_of_work: InMemoryUnitOfWork,
):
    from assistencia_manager.application.services.client_service import ClientService
    from assistencia_manager.application.services.equipment_service import EquipmentService

    identifier = EntityId.new()

    with pytest.raises(EntityNotFoundError):
        ClientService(lambda: unit_of_work).get(identifier)
    with pytest.raises(EntityNotFoundError):
        ClientService(lambda: unit_of_work).deactivate(identifier)
    with pytest.raises(EntityNotFoundError):
        EquipmentService(lambda: unit_of_work).get(identifier)
    with pytest.raises(EntityNotFoundError):
        EquipmentService(lambda: unit_of_work).deactivate(identifier)


def test_client_search_returns_filtered_page():
    from assistencia_manager.application.dto.client import CreateClientCommand, ClientSearchQuery
    from assistencia_manager.application.services.client_service import ClientService

    unit_of_work = InMemoryUnitOfWork()
    service = ClientService(lambda: unit_of_work)
    service.create(CreateClientCommand(name="Alpha"))
    service.create(CreateClientCommand(name="Beta"))
    service.create(CreateClientCommand(name="Alpine"))

    page = service.search(ClientSearchQuery(search="alp", page=1, page_size=1))

    assert page.items[0].name == "Alpha"
    assert page.page == 1
    assert page.page_size == 1
    assert page.total_items == 2
    assert page.total_pages == 2


def test_equipment_search_filters_by_text_and_client():
    from assistencia_manager.application.dto.client import CreateClientCommand
    from assistencia_manager.application.dto.equipment import (
        CreateEquipmentCommand,
        EquipmentSearchQuery,
    )
    from assistencia_manager.application.services.client_service import ClientService
    from assistencia_manager.application.services.equipment_service import EquipmentService

    unit_of_work = InMemoryUnitOfWork()
    client_service = ClientService(lambda: unit_of_work)
    equipment_service = EquipmentService(lambda: unit_of_work)
    first_client = client_service.create(CreateClientCommand(name="Primeiro"))
    second_client = client_service.create(CreateClientCommand(name="Segundo"))
    equipment_service.create(
        CreateEquipmentCommand(client_id=first_client.id, equipment_type="Notebook", model="A")
    )
    equipment_service.create(
        CreateEquipmentCommand(client_id=second_client.id, equipment_type="Notebook", model="B")
    )

    page = equipment_service.search(
        EquipmentSearchQuery(search="notebook", client_id=first_client.id, page=1, page_size=10)
    )

    assert [item.model for item in page.items] == ["A"]
    assert page.total_items == 1
