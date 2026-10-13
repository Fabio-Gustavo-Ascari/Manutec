from __future__ import annotations

from collections.abc import Callable

from assistencia_manager.application.dto.equipment import (
    CreateEquipmentCommand,
    UpdateEquipmentCommand,
)
from assistencia_manager.domain.entities.equipment import Equipment
from assistencia_manager.domain.exceptions import EntityNotFoundError
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
            return equipment
