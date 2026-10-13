from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from assistencia_manager.domain.entities.base import EntityStatus
from assistencia_manager.domain.entities.equipment import Equipment
from assistencia_manager.domain.identifiers import EntityId
from assistencia_manager.infrastructure.database.models.equipment import EquipmentModel


class SqlAlchemyEquipmentRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, entity: Equipment) -> None:
        self._session.merge(
            EquipmentModel(
                id=str(entity.id),
                status=entity.status.value,
                client_id=str(entity.client_id),
                equipment_type=entity.equipment_type,
                brand=entity.brand,
                model=entity.model,
                serial_number=entity.serial_number,
                accessories=list(entity.accessories),
            )
        )

    def get(self, identifier: EntityId) -> Equipment | None:
        model = self._session.get(EquipmentModel, str(identifier))
        if model is None:
            return None
        return self._to_entity(model)

    def list(self) -> tuple[Equipment, ...]:
        return tuple(
            self._to_entity(model) for model in self._session.scalars(select(EquipmentModel))
        )

    def remove(self, identifier: EntityId) -> None:
        model = self._session.get(EquipmentModel, str(identifier))
        if model is not None:
            self._session.delete(model)

    def exists_by_serial_number(self, serial_number: str) -> bool:
        return (
            self._session.scalar(
                select(EquipmentModel.id)
                .where(EquipmentModel.serial_number == serial_number)
                .limit(1)
            )
            is not None
        )

    @staticmethod
    def _to_entity(model: EquipmentModel) -> Equipment:
        return Equipment(
            id=EntityId.from_str(model.id),
            status=EntityStatus(model.status),
            client_id=EntityId.from_str(model.client_id),
            equipment_type=model.equipment_type,
            brand=model.brand,
            model=model.model,
            serial_number=model.serial_number,
            accessories=tuple(model.accessories or ()),
        )
