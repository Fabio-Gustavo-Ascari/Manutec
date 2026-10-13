from __future__ import annotations

import sqlite3
from datetime import datetime, timezone

import pytest
from sqlalchemy import inspect

from assistencia_manager.bootstrap import initialize_database
from assistencia_manager.infrastructure.config.paths import AppPaths
from assistencia_manager.infrastructure.integrity import IntegrityService


def test_e06_migration_adds_work_order_deadline_column(tmp_path):
    paths = AppPaths(tmp_path, tmp_path / "data", tmp_path / "app.db", tmp_path / "logs", tmp_path / "backups")
    engine = initialize_database(paths)
    assert "due_at" in {column["name"] for column in inspect(engine).get_columns("work_orders")}
    engine.dispose()


def test_integrity_service_detects_valid_and_corrupt_database(tmp_path):
    database = tmp_path / "app.db"
    connection = sqlite3.connect(database)
    connection.execute("CREATE TABLE sample (id INTEGER PRIMARY KEY)")
    connection.commit()
    connection.close()
    assert IntegrityService().check(database).ok
    database.write_bytes(b"not sqlite")
    result = IntegrityService().check(database)
    assert not result.ok


def test_backup_rejects_incompatible_manifest(tmp_path):
    from assistencia_manager.application.services.backup_service import BackupService

    database = tmp_path / "app.db"
    connection = sqlite3.connect(database)
    connection.execute("CREATE TABLE sample (id INTEGER PRIMARY KEY)")
    connection.commit()
    connection.close()
    backup = BackupService(database, tmp_path / "backups", application_version="0.1.0").create()
    with pytest.raises(ValueError, match="incompatível"):
        BackupService(database, tmp_path / "backups", application_version="0.2.0").restore(backup)
