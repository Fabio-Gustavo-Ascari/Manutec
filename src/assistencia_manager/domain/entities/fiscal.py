from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from assistencia_manager.domain.exceptions import DomainValidationError
from assistencia_manager.domain.identifiers import EntityId


class FiscalEnvironment(Enum):
    HOMOLOGATION = "homologation"
    PRODUCTION = "production"


class FiscalDocumentType(Enum):
    NFE = "nfe"
    NFCE = "nfce"
    NFSE = "nfse"


class FiscalDocumentStatus(Enum):
    AUTHORIZED = "authorized"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


@dataclass(slots=True)
class FiscalConfiguration:
    company_document: str
    state_registration: str | None = None
    municipal_registration: str | None = None
    environment: FiscalEnvironment = FiscalEnvironment.HOMOLOGATION
    provider: str = "simulated"
    certificate_path: str | None = None
    certificate_secret: str | None = None

    def __post_init__(self) -> None:
        if not self.company_document.strip():
            raise DomainValidationError("Documento fiscal da empresa é obrigatório")
        if not self.provider.strip():
            raise DomainValidationError("Provedor fiscal é obrigatório")
        if not isinstance(self.environment, FiscalEnvironment):
            raise DomainValidationError("Ambiente fiscal inválido")
        self.company_document = self.company_document.strip()
        self.provider = self.provider.strip().lower()


@dataclass(slots=True)
class FiscalDocument:
    document_type: FiscalDocumentType
    environment: FiscalEnvironment
    provider: str
    access_key: str
    status: FiscalDocumentStatus
    payload: dict[str, object] = field(default_factory=dict)
    rejection_reason: str | None = None
    id: EntityId = field(default_factory=EntityId.new)
    issued_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not isinstance(self.document_type, FiscalDocumentType):
            raise DomainValidationError("Tipo de documento fiscal inválido")
        if not isinstance(self.environment, FiscalEnvironment):
            raise DomainValidationError("Ambiente fiscal inválido")
        if not self.access_key.strip():
            raise DomainValidationError("Chave fiscal é obrigatória")

