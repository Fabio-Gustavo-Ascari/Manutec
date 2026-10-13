from __future__ import annotations

import logging
import os
import sqlite3

import pytest

from assistencia_manager.infrastructure.backup import BackupService
from assistencia_manager.infrastructure.logging import SanitizingFilter


def _create_database(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE sample (value TEXT)")
    connection.execute("INSERT INTO sample VALUES ('old')")
    connection.commit()
    connection.close()


def test_backup_rejects_a_corrupt_database_before_creating_an_archive(tmp_path):
    database = tmp_path / "data" / "app.db"
    database.parent.mkdir()
    database.write_bytes(b"not sqlite")

    with pytest.raises(ValueError, match="SQLite"):
        BackupService(database, tmp_path / "backups", application_version="0.1.0").create()

    assert not list((tmp_path / "backups").glob("*.zip"))


def test_restore_rolls_back_when_installing_the_validated_database_fails(tmp_path, monkeypatch):
    database = tmp_path / "data" / "app.db"
    _create_database(database)
    service = BackupService(database, tmp_path / "backups", application_version="0.1.0")
    backup = service.create()

    original_replace = os.replace
    calls = 0

    def fail_install(source, destination):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("disk full")
        return original_replace(source, destination)

    monkeypatch.setattr("assistencia_manager.infrastructure.backup.os.replace", fail_install)
    with pytest.raises(OSError, match="disk full"):
        service.restore(backup)

    connection = sqlite3.connect(database)
    assert connection.execute("SELECT value FROM sample").fetchone()[0] == "old"
    connection.close()


def test_log_filter_formats_and_redacts_parameterized_sensitive_values():
    record = logging.LogRecord(
        "assistencia_manager", logging.INFO, __file__, 1, "document=%s arquivo=%s", ("123", "app.db"), None
    )

    assert SanitizingFilter().filter(record)
    assert record.getMessage() == "document=[REDACTED] arquivo=app.db"
