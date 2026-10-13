from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from assistencia_manager.infrastructure.database.models.app_metadata import AppMetadata


class SqlAlchemyAppMetadataRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_all(self) -> dict[str, str]:
        return {row.key: row.value for row in self._session.scalars(select(AppMetadata))}

    def set_many(self, values: dict[str, str]) -> None:
        for key, value in values.items():
            row = self._session.get(AppMetadata, key)
            if row is None:
                self._session.add(AppMetadata(key=key, value=value))
            else:
                row.value = value

    def commit(self) -> None:
        self._session.commit()

    def close(self) -> None:
        self._session.close()
