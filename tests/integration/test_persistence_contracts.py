from sqlalchemy import text

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
