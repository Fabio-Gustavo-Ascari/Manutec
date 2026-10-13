from __future__ import annotations

from dataclasses import dataclass, field
from collections.abc import Iterable

from assistencia_manager.domain.entities.base import Entity
from assistencia_manager.domain.exceptions import DomainValidationError


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
class Client(Entity):
    """Cliente cadastrado para uso em ordens de serviço."""

    name: str = ""
    contacts: tuple[str, ...] = field(default_factory=tuple)
    document: str | None = None
    address: str | None = None
    notes: str | None = None

    def __post_init__(self) -> None:
        self.name = _required_text(self.name, "Nome")
        self.contacts = self._normalize_contacts(self.contacts)
        self.document = _optional_text(self.document)
        self.address = _optional_text(self.address)
        self.notes = _optional_text(self.notes)

    @staticmethod
    def _normalize_contacts(contacts: Iterable[str]) -> tuple[str, ...]:
        if isinstance(contacts, str):
            raise DomainValidationError("Contatos devem ser uma coleção de textos")
        try:
            normalized = tuple(item.strip() for item in contacts if item.strip())
        except (AttributeError, TypeError) as error:
            raise DomainValidationError("Contatos devem ser uma coleção de textos") from error
        return normalized

    def update(
        self,
        *,
        name: str | None = None,
        contacts: Iterable[str] | None = None,
        document: str | None = None,
        address: str | None = None,
        notes: str | None = None,
    ) -> None:
        if name is not None:
            self.name = _required_text(name, "Nome")
        if contacts is not None:
            self.contacts = self._normalize_contacts(contacts)
        if document is not None:
            self.document = _optional_text(document)
        if address is not None:
            self.address = _optional_text(address)
        if notes is not None:
            self.notes = _optional_text(notes)

