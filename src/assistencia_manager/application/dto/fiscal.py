from dataclasses import dataclass
from decimal import Decimal

from assistencia_manager.domain.entities.fiscal import FiscalDocumentType, FiscalEnvironment


@dataclass(frozen=True, slots=True)
class FiscalConfigurationCommand:
    company_document: str
    state_registration: str | None = None
    municipal_registration: str | None = None
    environment: FiscalEnvironment = FiscalEnvironment.HOMOLOGATION
    provider: str = "simulated"
    certificate_path: str | None = None
    certificate_secret: str | None = None


@dataclass(frozen=True, slots=True)
class IssueFiscalDocumentCommand:
    document_type: FiscalDocumentType
    number: int
    total: Decimal
    description: str

