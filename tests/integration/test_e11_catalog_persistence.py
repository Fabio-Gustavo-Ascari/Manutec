from decimal import Decimal

from assistencia_manager.application.dto.catalog import CreateCatalogCommand, CreateServiceCommand
from assistencia_manager.application.services.catalog_service import CatalogService
from assistencia_manager.domain.entities.catalog import CatalogType
from assistencia_manager.infrastructure.config.paths import AppPaths
from assistencia_manager.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork
from assistencia_manager.bootstrap import initialize_database


def test_e11_catalogs_persist_through_uow(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    engine = initialize_database(AppPaths.default())
    service = CatalogService(lambda: SqlAlchemyUnitOfWork(engine))

    supplier = service.create_catalog(CreateCatalogCommand(CatalogType.SUPPLIER, "Fornecedor Central", phone="11999999999"))
    item = service.create_service(CreateServiceCommand("Diagnóstico", Decimal("80"), warranty_days=30))

    assert service.search_catalogs(CatalogType.SUPPLIER, "central")[0].id == supplier.id
    with SqlAlchemyUnitOfWork(engine) as uow:
        persisted = uow.services.get(item.id)
        assert persisted is not None
        assert persisted.price == Decimal("80.00")
        assert persisted.warranty_days == 30
    engine.dispose()
