from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class IntegrityReport:
    ok: bool
    message: str


class IntegrityService:
    def check(self, database: Path) -> IntegrityReport:
        connection = None
        try:
            connection = sqlite3.connect(database)
            result = connection.execute("PRAGMA integrity_check").fetchone()[0]
            return IntegrityReport(result == "ok", str(result))
        except (OSError, sqlite3.Error) as error:
            return IntegrityReport(False, f"Falha na verificação: {error}")
        finally:
            if connection is not None:
                connection.close()
