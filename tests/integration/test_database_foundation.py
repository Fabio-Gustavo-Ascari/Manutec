from pathlib import Path

from sqlalchemy import text

from assistencia_manager.bootstrap import initialize_database
from assistencia_manager.infrastructure.config.paths import AppPaths
from assistencia_manager.infrastructure.database.base import Base
from assistencia_manager.infrastructure.database.engine import create_engine
from assistencia_manager.infrastructure.database.models import AppMetadata
from assistencia_manager.infrastructure.database.session import create_session_factory


def test_default_database_path_uses_local_app_data(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    paths = AppPaths.default()

    assert paths.root == Path(tmp_path) / "Manutec"
    assert paths.database == paths.root / "data" / "assistencia.db"


def test_engine_creates_database_and_configures_sqlite(tmp_path):
    database = tmp_path / "data" / "assistencia.db"

    engine = create_engine(database)
    with engine.connect() as connection:
        foreign_keys = connection.execute(text("PRAGMA foreign_keys")).scalar_one()
        journal_mode = connection.execute(text("PRAGMA journal_mode")).scalar_one()
        synchronous = connection.execute(text("PRAGMA synchronous")).scalar_one()

    assert database.exists()
    assert foreign_keys == 1
    assert journal_mode.lower() == "wal"
    assert synchronous == 2
    engine.dispose()


def test_data_persists_after_engine_reinitialization(tmp_path):
    database = tmp_path / "assistencia.db"

    first_engine = create_engine(database)
    with first_engine.begin() as connection:
        connection.execute(text("CREATE TABLE settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)"))
        connection.execute(text("INSERT INTO settings (key, value) VALUES ('version', '0.1.0')"))
    first_engine.dispose()

    second_engine = create_engine(database)
    with second_engine.connect() as connection:
        value = connection.execute(text("SELECT value FROM settings WHERE key = 'version'")).scalar_one()
    second_engine.dispose()

    assert value == "0.1.0"


def test_metadata_contains_application_metadata_model():
    assert AppMetadata.__tablename__ == "app_metadata"
    assert "app_metadata" in Base.metadata.tables


def test_session_factory_creates_short_lived_sessions(tmp_path):
    engine = create_engine(tmp_path / "assistencia.db")
    factory = create_session_factory(engine)

    with factory() as session:
        assert session.bind is engine

    engine.dispose()


def test_initialize_database_applies_base_migration(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    paths = AppPaths.default()

    engine = initialize_database(paths)
    with engine.connect() as connection:
        tables = {
            row[0]
            for row in connection.execute(
                text("SELECT name FROM sqlite_master WHERE type = 'table'")
            )
        }

    assert paths.database.exists()
    assert "app_metadata" in tables
    engine.dispose()
