from decimal import Decimal

import pytest

from assistencia_manager.application.dto.fiscal import FiscalConfigurationCommand, IssueFiscalDocumentCommand
from assistencia_manager.application.services.fiscal_service import FiscalService
from assistencia_manager.domain.entities.fiscal import FiscalDocumentType, FiscalEnvironment
from assistencia_manager.domain.exceptions import DomainValidationError
from assistencia_manager.infrastructure.fiscal_adapters import (
    SimulatedPeripheralAdapter, fiscal_provider_factory,
)


class Metadata:
    def __init__(self):
        self.values = {}

    def get_all(self):
        return dict(self.values)

    def set_many(self, values):
        self.values.update(values)

    def commit(self):
        pass

    def close(self):
        pass


def test_configuration_is_persisted_without_certificate_secret_and_document_is_issued():
    metadata = Metadata()
    service = FiscalService(lambda: metadata, fiscal_provider_factory)
    configuration = service.configure(FiscalConfigurationCommand(
        company_document="12.345.678/0001-90",
        environment=FiscalEnvironment.HOMOLOGATION,
        certificate_secret="must-not-be-persisted",
    ))

    assert configuration.provider == "simulated"
    assert "must-not-be-persisted" not in metadata.values["fiscal.configuration"]
    document = service.issue(IssueFiscalDocumentCommand(
        FiscalDocumentType.NFCE, 10, Decimal("99.90"), "Venda de peça",
    ))
    assert document.status.value == "authorized"
    assert len(document.access_key) == 44


def test_fiscal_issue_requires_configuration_and_unknown_provider_is_rejected():
    service = FiscalService(lambda: Metadata(), fiscal_provider_factory)
    with pytest.raises(DomainValidationError, match="Configure"):
        service.issue(IssueFiscalDocumentCommand(FiscalDocumentType.NFE, 1, Decimal("10"), "Venda"))

    with pytest.raises(DomainValidationError, match="não está instalado"):
        service.configure(FiscalConfigurationCommand("123", provider="unknown"))


def test_simulated_peripherals_cover_printer_barcode_and_pix_failure_paths():
    adapter = SimulatedPeripheralAdapter()
    assert adapter.print_document("NFCE", "Caixa")
    assert adapter.read_barcode("789") == "789"
    assert "BR.GOV.BCB.PIX" in adapter.pix_qr_payload("pix@example.com", Decimal("12.50"))
    with pytest.raises(DomainValidationError):
        adapter.read_barcode("")
    with pytest.raises(DomainValidationError):
        adapter.pix_qr_payload("", Decimal("12.50"))
