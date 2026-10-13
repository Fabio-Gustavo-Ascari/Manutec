from __future__ import annotations

import json
from dataclasses import asdict
from collections.abc import Callable
from decimal import Decimal

from assistencia_manager.application.dto.fiscal import FiscalConfigurationCommand, IssueFiscalDocumentCommand
from assistencia_manager.domain.entities.fiscal import FiscalConfiguration, FiscalDocument
from assistencia_manager.domain.exceptions import DomainValidationError


class FiscalService:
    """Orquestra configuração fiscal e emissão por um adaptador de provedor."""

    def __init__(self, metadata_factory: Callable[[], object], provider_factory: Callable[[str], object]):
        self._metadata_factory = metadata_factory
        self._provider_factory = provider_factory

    def get_configuration(self) -> FiscalConfiguration | None:
        repository = self._metadata_factory()
        try:
            values = repository.get_all()
        finally:
            repository.close()
        raw = values.get("fiscal.configuration")
        if not raw:
            return None
        data = json.loads(raw)
        from assistencia_manager.domain.entities.fiscal import FiscalEnvironment
        return FiscalConfiguration(**{**data, "environment": FiscalEnvironment(data["environment"])})

    def configure(self, command: FiscalConfigurationCommand) -> FiscalConfiguration:
        configuration = FiscalConfiguration(**asdict(command))
        self._provider_factory(configuration.provider)
        repository = self._metadata_factory()
        try:
            data = {**asdict(configuration), "environment": configuration.environment.value}
            data.pop("certificate_secret", None)
            repository.set_many({"fiscal.configuration": json.dumps(data, sort_keys=True)})
            repository.commit()
        finally:
            repository.close()
        return configuration

    def issue(self, command: IssueFiscalDocumentCommand) -> FiscalDocument:
        configuration = self.get_configuration()
        if configuration is None:
            raise DomainValidationError("Configure o ambiente fiscal antes de emitir")
        if command.number <= 0:
            raise DomainValidationError("Número fiscal deve ser maior que zero")
        total = Decimal(str(command.total)).quantize(Decimal("0.01"))
        if total <= 0 or not command.description.strip():
            raise DomainValidationError("Documento fiscal inválido")
        provider = self._provider_factory(configuration.provider)
        return provider.issue(configuration, command.document_type, command.number, total, command.description)

