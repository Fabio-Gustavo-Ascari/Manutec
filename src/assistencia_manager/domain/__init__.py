"""Entidades, regras, identificadores e contratos do domínio."""

from assistencia_manager.domain.exceptions import DomainError, DomainValidationError
from assistencia_manager.domain.entities import Entity, EntityStatus
from assistencia_manager.domain.identifiers import EntityId

__all__ = ["DomainError", "DomainValidationError", "Entity", "EntityId", "EntityStatus"]
