from __future__ import annotations

from sqlalchemy import inspect

from assistencia_manager.bootstrap import initialize_database
from assistencia_manager.infrastructure.config.paths import AppPaths
from assistencia_manager.infrastructure.database.models import ClientModel, EquipmentModel


def test_business_models_define_expected_tables_and_relationship_columns():
    assert ClientModel.__tablename__ == "clients"
    assert EquipmentModel.__tablename__ == "equipment"
    assert "client_id" in EquipmentModel.__table__.c
    assert EquipmentModel.__table__.c.client_id.nullable is False


def test_database_migration_creates_business_tables_and_foreign_key(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))

    engine = initialize_database(AppPaths.default())
    database_inspector = inspect(engine)

    assert {"app_metadata", "clients", "equipment"}.issubset(
        set(database_inspector.get_table_names())
    )
    foreign_keys = database_inspector.get_foreign_keys("equipment")
    assert any(
        foreign_key["referred_table"] == "clients"
        and foreign_key["constrained_columns"] == ["client_id"]
        for foreign_key in foreign_keys
    )
    engine.dispose()
