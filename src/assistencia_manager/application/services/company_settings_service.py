from __future__ import annotations

from collections.abc import Callable, Mapping

from assistencia_manager.domain.exceptions import DomainValidationError


class CompanySettingsService:
    FIELDS = ("name", "document", "address", "phone", "email")

    def __init__(self, repository_factory: Callable[[], object]) -> None:
        self._repository_factory = repository_factory

    def get(self) -> dict[str, str]:
        repository = self._repository_factory()
        try:
            values = repository.get_all()
            return {field: values.get(f"company.{field}", "") for field in self.FIELDS}
        finally:
            close = getattr(repository, "close", None)
            if close:
                close()

    def update(self, values: Mapping[str, str]) -> dict[str, str]:
        unknown = set(values) - set(self.FIELDS)
        if unknown:
            raise DomainValidationError("Configuração desconhecida")
        normalized = {field: str(values.get(field, "")).strip() for field in self.FIELDS}
        if not normalized["name"]:
            raise DomainValidationError("Nome da empresa é obrigatório")
        repository = self._repository_factory()
        try:
            repository.set_many({f"company.{field}": value for field, value in normalized.items()})
            repository.commit()
        finally:
            close = getattr(repository, "close", None)
            if close:
                close()
        return normalized
