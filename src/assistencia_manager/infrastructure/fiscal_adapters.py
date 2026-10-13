from __future__ import annotations

import hashlib
from decimal import Decimal

from assistencia_manager.domain.entities.fiscal import (
    FiscalConfiguration, FiscalDocument, FiscalDocumentStatus, FiscalDocumentType,
)
from assistencia_manager.domain.exceptions import DomainValidationError


class SimulatedFiscalProvider:
    """Adaptador determinístico para homologação e testes sem rede ou certificado real."""

    name = "simulated"

    def issue(self, configuration: FiscalConfiguration, document_type: FiscalDocumentType, number: int,
              total: Decimal, description: str) -> FiscalDocument:
        if configuration.provider != self.name:
            raise DomainValidationError("Provedor fiscal não suportado")
        seed = f"{configuration.company_document}|{configuration.environment.value}|{document_type.value}|{number}|{total}"
        access_key = hashlib.sha256(seed.encode()).hexdigest()[:44]
        return FiscalDocument(document_type, configuration.environment, self.name, access_key,
                              FiscalDocumentStatus.AUTHORIZED,
                              {"number": number, "total": str(total), "description": description.strip()})


class SimulatedPeripheralAdapter:
    """Saída segura para testes de impressora, leitor e QR Code sem hardware real."""

    def print_document(self, content: str, printer_name: str) -> bool:
        return bool(content.strip() and printer_name.strip())

    def read_barcode(self, value: str) -> str:
        value = value.strip()
        if not value:
            raise DomainValidationError("Código de barras vazio")
        return value

    def pix_qr_payload(self, key: str, amount: Decimal) -> str:
        amount = Decimal(str(amount)).quantize(Decimal("0.01"))
        if not key.strip() or amount <= 0:
            raise DomainValidationError("Dados do QR Code PIX inválidos")
        return f"000201|BR.GOV.BCB.PIX|{key.strip()}|{amount}"


def fiscal_provider_factory(name: str) -> SimulatedFiscalProvider:
    if name != SimulatedFiscalProvider.name:
        raise DomainValidationError(f"Provedor fiscal '{name}' não está instalado")
    return SimulatedFiscalProvider()

