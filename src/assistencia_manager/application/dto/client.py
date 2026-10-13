from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from assistencia_manager.domain.exceptions import DomainValidationError
from assistencia_manager.domain.identifiers import EntityId


@dataclass(frozen=True, slots=True)
class CreateClientCommand:
    name: str
    contacts: Iterable[str] = field(default_factory=tuple)
    document: str | None = None
    address: str | None = None
    notes: str | None = None


@dataclass(frozen=True, slots=True)
class UpdateClientCommand:
    identifier: EntityId
    name: str | None = None
    contacts: Iterable[str] | None = None
    document: str | None = None
    address: str | None = None
    notes: str | None = None


@dataclass(frozen=True, slots=True)
class ClientSearchQuery:
    search: str | None = None
    page: int = 1
    page_size: int = 20

    def __post_init__(self) -> None:
        if self.page < 1:
            raise DomainValidationError("Página deve ser maior ou igual a 1")
        if not 1 <= self.page_size <= 100:
            raise DomainValidationError("Tamanho da página deve estar entre 1 e 100")
