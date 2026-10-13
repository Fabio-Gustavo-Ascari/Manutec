class DomainError(Exception):
    """Base para erros esperados nas regras do domínio."""


class DomainValidationError(DomainError, ValueError):
    """Indica que um valor não respeita uma invariante do domínio."""


class EntityNotFoundError(DomainError):
    """Indica que uma entidade solicitada não existe."""


class DuplicateEntityError(DomainError):
    """Indica conflito com uma entidade já existente."""


class InactiveEntityError(DomainError):
    """Indica tentativa de usar uma entidade inativada."""


class TransactionError(DomainError):
    """Indica falha ao concluir uma unidade de trabalho."""

