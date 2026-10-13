from sqlalchemy import text

from assistencia_manager.application.dto.client import (
    ClientSearchQuery,
    CreateClientCommand,
    UpdateClientCommand,
)
from assistencia_manager.application.dto.equipment import (
    CreateEquipmentCommand,
    EquipmentSearchQuery,
)
from assistencia_manager.application.services.client_service import ClientService
from assistencia_manager.application.services.equipment_service import EquipmentService
from assistencia_manager.bootstrap import initialize_database
from assistencia_manager.infrastructure.config.paths import AppPaths
from assistencia_manager.infrastructure.database.engine import create_engine
from assistencia_manager.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from assistencia_manager.infrastructure.database.repositories import (
    SqlAlchemyClientRepository,
    SqlAlchemyEquipmentRepository,
)


def test_unit_of_work_commits_changes_when_context_exits_successfully(tmp_path):
    engine = create_engine(tmp_path / "assistencia.db")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE events (name TEXT NOT NULL)"))

    with SqlAlchemyUnitOfWork(engine) as unit_of_work:
        unit_of_work.session.execute(text("INSERT INTO events (name) VALUES ('created')"))

    with engine.connect() as connection:
        assert connection.execute(text("SELECT name FROM events")).scalar_one() == "created"
    engine.dispose()


def test_unit_of_work_rolls_back_changes_when_context_fails(tmp_path):
    engine = create_engine(tmp_path / "assistencia.db")
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE events (name TEXT NOT NULL)"))

    try:
        with SqlAlchemyUnitOfWork(engine) as unit_of_work:
            unit_of_work.session.execute(text("INSERT INTO events (name) VALUES ('discarded')"))
            raise RuntimeError("failure")
    except RuntimeError:
        pass

    with engine.connect() as connection:
        assert connection.execute(text("SELECT COUNT(*) FROM events")).scalar_one() == 0
    engine.dispose()


def test_unit_of_work_exposes_business_repositories(tmp_path):
    engine = create_engine(tmp_path / "assistencia.db")

    with SqlAlchemyUnitOfWork(engine) as unit_of_work:
        assert isinstance(unit_of_work.clients, SqlAlchemyClientRepository)
        assert isinstance(unit_of_work.equipment, SqlAlchemyEquipmentRepository)

    engine.dispose()


def test_client_service_persists_update_and_deactivation(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    engine = initialize_database(AppPaths.default())
    service = ClientService(lambda: SqlAlchemyUnitOfWork(engine))

    client = service.create(CreateClientCommand(name="Antigo"))
    service.update(UpdateClientCommand(identifier=client.id, name="Novo"))
    service.deactivate(client.id)

    with SqlAlchemyUnitOfWork(engine) as unit_of_work:
        loaded = unit_of_work.clients.get(client.id)

        assert loaded is not None
        assert loaded.name == "Novo"
        assert loaded.status.value == "inactive"

    engine.dispose()


def test_services_search_persisted_entities_with_pagination(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    engine = initialize_database(AppPaths.default())
    client_service = ClientService(lambda: SqlAlchemyUnitOfWork(engine))
    equipment_service = EquipmentService(lambda: SqlAlchemyUnitOfWork(engine))

    first_client = client_service.create(CreateClientCommand(name="Alpha"))
    client_service.create(CreateClientCommand(name="Beta"))
    equipment_service.create(
        CreateEquipmentCommand(
            client_id=first_client.id,
            equipment_type="Notebook",
            model="A",
        )
    )

    clients = client_service.search(ClientSearchQuery(search="a", page=1, page_size=1))
    equipment = equipment_service.search(
        EquipmentSearchQuery(search="note", client_id=first_client.id, page=1, page_size=10)
    )

    assert clients.items[0].name == "Alpha"
    assert clients.total_items == 2
    assert clients.total_pages == 2
    assert [item.model for item in equipment.items] == ["A"]
    assert equipment.total_items == 1

    engine.dispose()
