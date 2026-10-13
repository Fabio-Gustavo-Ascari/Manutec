"""Exceções de domínio do Manutec."""
from assistencia_manager.domain.exceptions.errors import (
    DomainError,
    DomainValidationError,
    DuplicateEntityError,
    EntityNotFoundError,
    InactiveEntityError,
    TransactionError,
)

__all__ = [
    "DomainError",
    "DomainValidationError",
    "DuplicateEntityError",
    "EntityNotFoundError",
    "InactiveEntityError",
    "TransactionError",
]
