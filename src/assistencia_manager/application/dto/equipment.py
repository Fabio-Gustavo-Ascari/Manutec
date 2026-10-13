from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from assistencia_manager.domain.identifiers import EntityId


@dataclass(frozen=True, slots=True)
class CreateEquipmentCommand:
    client_id: EntityId
    equipment_type: str
    brand: str | None = None
    model: str | None = None
    serial_number: str | None = None
    accessories: Iterable[str] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class UpdateEquipmentCommand:
    identifier: EntityId
    equipment_type: str | None = None
    brand: str | None = None
    model: str | None = None
    serial_number: str | None = None
    accessories: Iterable[str] | None = None
