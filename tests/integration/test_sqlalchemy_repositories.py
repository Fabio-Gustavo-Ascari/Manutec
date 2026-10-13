from __future__ import annotations

from assistencia_manager.domain.entities.client import Client
from assistencia_manager.domain.entities.equipment import Equipment
from assistencia_manager.domain.identifiers import EntityId
from assistencia_manager.infrastructure.database.engine import create_engine
from assistencia_manager.infrastructure.database.repositories import (
    SqlAlchemyClientRepository,
    SqlAlchemyEquipmentRepository,
)
from assistencia_manager.infrastructure.database.session import create_session_factory


def test_client_repository_persists_and_rehydrates_client(tmp_path):
    engine = create_engine(tmp_path / "assistencia.db")
    from assistencia_manager.infrastructure.database.base import Base
    from assistencia_manager.infrastructure.database.models import ClientModel, EquipmentModel

    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)
    client = Client(
        name="Oficina Central",
        contacts=("11 9999",),
        document="123",
    )

    with session_factory() as session:
        repository = SqlAlchemyClientRepository(session)
        repository.add(client)
        session.commit()

    with session_factory() as session:
        repository = SqlAlchemyClientRepository(session)
        loaded = repository.get(client.id)

        assert loaded is not None
        assert loaded.id == client.id
        assert loaded.name == client.name
        assert loaded.contacts == client.contacts
        assert repository.exists_by_name("Oficina Central")
        assert not repository.exists_by_name("Inexistente")

    engine.dispose()


def test_equipment_repository_persists_client_link_and_lists_equipment(tmp_path):
    engine = create_engine(tmp_path / "assistencia.db")
    from assistencia_manager.infrastructure.database.base import Base

    Base.metadata.create_all(engine)
    session_factory = create_session_factory(engine)
    client_id = EntityId.new()
    equipment = Equipment(
        client_id=client_id,
        equipment_type="Notebook",
        accessories=("Fonte",),
        serial_number="ABC-123",
    )

    with session_factory() as session:
        session.execute(
            __import__("sqlalchemy").text(
                "INSERT INTO clients (id, status, name, contacts) VALUES (:id, :status, :name, :contacts)"
            ),
            {"id": str(client_id), "status": "active", "name": "Cliente", "contacts": "[]"},
        )
        repository = SqlAlchemyEquipmentRepository(session)
        repository.add(equipment)
        session.commit()

    with session_factory() as session:
        repository = SqlAlchemyEquipmentRepository(session)
        loaded = repository.get(equipment.id)

        assert loaded is not None
        assert loaded.client_id == client_id
        assert loaded.accessories == ("Fonte",)
        assert repository.exists_by_serial_number("ABC-123")
        assert tuple(repository.list()) == (loaded,)

    engine.dispose()
