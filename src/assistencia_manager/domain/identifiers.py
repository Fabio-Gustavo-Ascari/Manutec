from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

from assistencia_manager.domain.exceptions import DomainValidationError


@dataclass(frozen=True, slots=True)
class EntityId:
    """Identificador estável e serializável das entidades do domínio."""

    value: UUID

    def __post_init__(self) -> None:
        if not isinstance(self.value, UUID):
            raise DomainValidationError("Identificador deve ser um UUID válido")

    @classmethod
    def new(cls) -> EntityId:
        return cls(uuid4())

    @classmethod
    def from_str(cls, value: str) -> EntityId:
        try:
            return cls(UUID(value))
        except (AttributeError, TypeError, ValueError) as error:
            raise DomainValidationError("Identificador deve ser um UUID válido") from error

    def __str__(self) -> str:
        return str(self.value)

