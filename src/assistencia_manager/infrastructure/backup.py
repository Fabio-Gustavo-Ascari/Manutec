from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path


class BackupService:
    def __init__(self, database: Path, backup_directory: Path, *, application_version: str) -> None:
        self.database = Path(database)
        self.backup_directory = Path(backup_directory)
        self.application_version = application_version

    def create(self) -> Path:
        if not self.database.is_file():
            raise FileNotFoundError(self.database)
        self.backup_directory.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        name = f"manutec-backup-v{self.application_version}-{timestamp}.zip"
        digest = self._sha256(self.database)
        manifest = {"format": 1, "application_version": self.application_version, "database_sha256": digest}
        destination = self.backup_directory / name
        with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.write(self.database, "database.sqlite")
            archive.writestr("manifest.json", json.dumps(manifest, sort_keys=True))
        return destination

    def restore(self, backup: Path) -> Path:
        backup = Path(backup)
        with zipfile.ZipFile(backup) as archive:
            names = set(archive.namelist())
            if names != {"database.sqlite", "manifest.json"}:
                raise ValueError("Backup possui conteúdo inesperado")
            manifest = json.loads(archive.read("manifest.json"))
            if manifest.get("format") != 1 or manifest.get("application_version") != self.application_version:
                raise ValueError("Backup incompatível com a versão instalada")
            with tempfile.NamedTemporaryFile(delete=False, dir=self.database.parent, suffix=".restore") as stream:
                stream.write(archive.read("database.sqlite"))
                temporary = Path(stream.name)
        try:
            if self._sha256(temporary) != manifest.get("database_sha256"):
                raise ValueError("Checksum do backup não confere")
            self._validate_sqlite(temporary)
            self.database.parent.mkdir(parents=True, exist_ok=True)
            preserved = self.database.with_name(f"{self.database.name}.pre-restore-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}")
            if self.database.exists():
                os.replace(self.database, preserved)
            os.replace(temporary, self.database)
            return preserved
        finally:
            temporary.unlink(missing_ok=True)

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _validate_sqlite(path: Path) -> None:
        connection = None
        try:
            connection = sqlite3.connect(path)
            result = connection.execute("PRAGMA integrity_check").fetchone()[0]
        except sqlite3.Error as error:
            raise ValueError("Backup não contém um banco SQLite válido") from error
        finally:
            if connection is not None:
                connection.close()
        if result != "ok":
            raise ValueError(f"Integridade do backup inválida: {result}")
