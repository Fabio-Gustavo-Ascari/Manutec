from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

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
