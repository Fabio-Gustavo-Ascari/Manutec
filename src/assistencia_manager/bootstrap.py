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

    config_path = Path(__file__).resolve().parents[2] / "alembic.ini"
    config = Config(str(config_path.resolve()))
    config.set_main_option("script_location", str(Path(__file__).parent / "infrastructure" / "migrations"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{paths.database.as_posix()}")
    command.upgrade(config, "head")
    return engine
