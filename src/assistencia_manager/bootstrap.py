from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config

from assistencia_manager.infrastructure.config.paths import AppPaths
from assistencia_manager.infrastructure.database.engine import create_engine


def initialize_database(paths: AppPaths | None = None):
    paths = paths or AppPaths.default()
    paths.ensure_directories()
    engine = create_engine(paths.database)

    # The migration package is bundled with the executable.  Do not resolve
    # alembic.ini from the repository root: that file is not present in a
    # PyInstaller installation.
    config = Config()
    config.set_main_option("script_location", str(Path(__file__).parent / "infrastructure" / "migrations"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{paths.database.as_posix()}")
    command.upgrade(config, "head")
    return engine
