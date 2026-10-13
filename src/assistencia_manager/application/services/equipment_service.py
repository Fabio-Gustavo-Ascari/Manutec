from __future__ import annotations

from collections.abc import Callable
from collections.abc import Sequence

from assistencia_manager.application.dto.equipment import (
    CreateEquipmentCommand,
    EquipmentSearchQuery,
    UpdateEquipmentCommand,
)
from assistencia_manager.application.dto.pagination import Page
from assistencia_manager.domain.entities.equipment import Equipment
from assistencia_manager.domain.exceptions import EntityNotFoundError
from assistencia_manager.domain.identifiers import EntityId
from assistencia_manager.domain.unit_of_work import UnitOfWork


class EquipmentService:
    def __init__(self, unit_of_work_factory: Callable[[], UnitOfWork]) -> None:
        self._unit_of_work_factory = unit_of_work_factory

    def create(self, command: CreateEquipmentCommand) -> Equipment:
        with self._unit_of_work_factory() as unit_of_work:
            if unit_of_work.clients.get(command.client_id) is None:
                raise EntityNotFoundError(f"Cliente {command.client_id} não encontrado")
            equipment = Equipment(
                client_id=command.client_id,
                equipment_type=command.equipment_type,
                brand=command.brand,
                model=command.model,
                serial_number=command.serial_number,
                accessories=command.accessories,
            )
            unit_of_work.equipment.add(equipment)
            return equipment

    def update(self, command: UpdateEquipmentCommand) -> Equipment:
        with self._unit_of_work_factory() as unit_of_work:
            equipment = unit_of_work.equipment.get(command.identifier)
            if equipment is None:
                raise EntityNotFoundError(f"Equipamento {command.identifier} não encontrado")
            equipment.update(
                equipment_type=command.equipment_type,
                brand=command.brand,
                model=command.model,
                serial_number=command.serial_number,
                accessories=command.accessories,
            )
            unit_of_work.equipment.add(equipment)
            return equipment

    def get(self, identifier: EntityId) -> Equipment:
        with self._unit_of_work_factory() as unit_of_work:
            equipment = unit_of_work.equipment.get(identifier)
            if equipment is None:
                raise EntityNotFoundError(f"Equipamento {identifier} não encontrado")
            return equipment

    def list(self) -> Sequence[Equipment]:
        with self._unit_of_work_factory() as unit_of_work:
            return tuple(unit_of_work.equipment.list())

    def deactivate(self, identifier: EntityId) -> Equipment:
        with self._unit_of_work_factory() as unit_of_work:
            equipment = unit_of_work.equipment.get(identifier)
            if equipment is None:
                raise EntityNotFoundError(f"Equipamento {identifier} não encontrado")
            equipment.deactivate()
            unit_of_work.equipment.add(equipment)
            return equipment

    def search(self, query: EquipmentSearchQuery) -> Page[Equipment]:
        with self._unit_of_work_factory() as unit_of_work:
            offset = (query.page - 1) * query.page_size
            items = unit_of_work.equipment.search(
                query.search, query.client_id, offset, query.page_size
            )
            return Page(
                items=tuple(items),
                page=query.page,
                page_size=query.page_size,
                total_items=unit_of_work.equipment.count(query.search, query.client_id),
            )
