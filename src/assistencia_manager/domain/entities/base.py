from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from assistencia_manager.domain.exceptions import InactiveEntityError
from assistencia_manager.domain.identifiers import EntityId


class EntityStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


@dataclass(eq=False, slots=True)
class Entity:
    """Base para entidades com identidade e inativação lógica."""

    id: EntityId = field(default_factory=EntityId.new)
    status: EntityStatus = EntityStatus.ACTIVE

    def __eq__(self, other: object) -> bool:
        return isinstance(other, type(self)) and self.id == other.id

    def __hash__(self) -> int:
        return hash((type(self), self.id))

    def activate(self) -> None:
        self.status = EntityStatus.ACTIVE

    def deactivate(self) -> None:
        self.status = EntityStatus.INACTIVE

    def ensure_active(self) -> None:
        if self.status is EntityStatus.INACTIVE:
            raise InactiveEntityError(f"Entidade {self.id} está inativa")

