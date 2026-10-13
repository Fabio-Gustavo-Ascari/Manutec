from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from assistencia_manager.domain.entities.base import Entity
from assistencia_manager.domain.exceptions import DomainValidationError
from assistencia_manager.domain.identifiers import EntityId


def _required_text(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise DomainValidationError(f"{field_name} deve ser texto")
    cleaned = value.strip()
    if not cleaned:
        raise DomainValidationError(f"{field_name} não pode ser vazio")
    return cleaned


def _optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise DomainValidationError("Valor opcional deve ser texto")
    cleaned = value.strip()
    return cleaned or None


@dataclass(eq=False, slots=True)
class Equipment(Entity):
    """Equipamento pertencente a um cliente."""

    client_id: EntityId | None = None
    equipment_type: str = ""
    brand: str | None = None
    model: str | None = None
    serial_number: str | None = None
    accessories: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not isinstance(self.client_id, EntityId):
            raise DomainValidationError("Equipamento deve possuir um cliente válido")
        self.equipment_type = _required_text(self.equipment_type, "Tipo do equipamento")
        self.brand = _optional_text(self.brand)
        self.model = _optional_text(self.model)
        self.serial_number = _optional_text(self.serial_number)
        self.accessories = self._normalize_accessories(self.accessories)

    @staticmethod
    def _normalize_accessories(accessories: Iterable[str]) -> tuple[str, ...]:
        if isinstance(accessories, str):
            raise DomainValidationError("Acessórios devem ser uma coleção de textos")
        try:
            normalized = tuple(item.strip() for item in accessories if item.strip())
        except (AttributeError, TypeError) as error:
            raise DomainValidationError("Acessórios devem ser uma coleção de textos") from error
        return normalized

    def update(
        self,
        *,
        equipment_type: str | None = None,
        brand: str | None = None,
        model: str | None = None,
        serial_number: str | None = None,
        accessories: Iterable[str] | None = None,
    ) -> None:
        if equipment_type is not None:
            self.equipment_type = _required_text(equipment_type, "Tipo do equipamento")
        if brand is not None:
            self.brand = _optional_text(brand)
        if model is not None:
            self.model = _optional_text(model)
        if serial_number is not None:
            self.serial_number = _optional_text(serial_number)
        if accessories is not None:
            self.accessories = self._normalize_accessories(accessories)

