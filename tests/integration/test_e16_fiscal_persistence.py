from decimal import Decimal

from assistencia_manager.application.dto.fiscal import FiscalConfigurationCommand, IssueFiscalDocumentCommand
from assistencia_manager.application.services.fiscal_service import FiscalService
from assistencia_manager.bootstrap import initialize_database
from assistencia_manager.domain.entities.fiscal import FiscalDocumentType, FiscalEnvironment
from assistencia_manager.infrastructure.config.paths import AppPaths
from assistencia_manager.infrastructure.database.repositories.app_metadata import SqlAlchemyAppMetadataRepository
from assistencia_manager.infrastructure.database.session import create_session_factory
from assistencia_manager.infrastructure.fiscal_adapters import fiscal_provider_factory


def test_fiscal_configuration_and_all_document_types_survive_database_round_trip(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    engine = initialize_database(AppPaths.default())
    metadata_factory = lambda: SqlAlchemyAppMetadataRepository(create_session_factory(engine)())
    service = FiscalService(metadata_factory, fiscal_provider_factory)
    service.configure(FiscalConfigurationCommand(
        "12.345.678/0001-90", environment=FiscalEnvironment.PRODUCTION,
    ))

    restored = FiscalService(metadata_factory, fiscal_provider_factory)
    assert restored.get_configuration().environment is FiscalEnvironment.PRODUCTION
    for document_type in FiscalDocumentType:
        document = restored.issue(IssueFiscalDocumentCommand(document_type, 1, Decimal("10.00"), "Teste"))
        assert document.status.value == "authorized"
    engine.dispose()
