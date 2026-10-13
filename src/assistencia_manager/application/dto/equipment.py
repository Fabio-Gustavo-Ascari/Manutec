from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from assistencia_manager.domain.exceptions import DomainValidationError
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


@dataclass(frozen=True, slots=True)
class EquipmentSearchQuery:
    search: str | None = None
    client_id: EntityId | None = None
    page: int = 1
    page_size: int = 20

    def __post_init__(self) -> None:
        if self.page < 1:
            raise DomainValidationError("Página deve ser maior ou igual a 1")
        if not 1 <= self.page_size <= 100:
            raise DomainValidationError("Tamanho da página deve estar entre 1 e 100")
