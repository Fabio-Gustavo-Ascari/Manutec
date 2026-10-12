from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class AppPaths:
    root: Path
    data: Path
    database: Path
    logs: Path
    backups: Path

    @classmethod
    def default(cls) -> AppPaths:
        local_app_data = os.environ.get("LOCALAPPDATA")
        base = Path(local_app_data) if local_app_data else Path.home() / "AppData" / "Local"
        root = base / "AssistenciaManager"
        return cls(
            root=root,
            data=root / "data",
            database=root / "data" / "assistencia.db",
            logs=root / "logs",
            backups=root / "backups",
        )

    def ensure_directories(self) -> None:
        for directory in (self.root, self.data, self.logs, self.backups):
            directory.mkdir(parents=True, exist_ok=True)
