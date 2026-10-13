from decimal import Decimal

import pytest
from dataclasses import dataclass, field
from types import SimpleNamespace

from assistencia_manager.application.dto.catalog import (
    CreateCatalogCommand,
    CreateServiceCommand,
    CreateServicePackageCommand,
    CreateWarrantyRuleCommand,
)
from assistencia_manager.application.services.catalog_service import CatalogService
from assistencia_manager.domain.entities.catalog import CatalogType
from assistencia_manager.domain.exceptions import DomainValidationError


class _Repo:
    def __init__(self): self.values = {}
    def add(self, value): self.values[value.id] = value
    def get(self, identifier): return self.values.get(identifier)
    def list(self): return tuple(self.values.values())
    def search(self, kind, term): return tuple(x for x in self.values.values() if x.kind is kind and (not term or term.casefold() in x.name.casefold()))


class _Uow:
    def __init__(self):
        self.catalogs = _Repo(); self.services = _Repo(); self.service_packages = _Repo(); self.warranty_rules = _Repo()
    def __enter__(self): return self
    def __exit__(self, *args): pass


@pytest.fixture
def fake_uow_factory():
    uow = _Uow()
    return lambda: uow


def test_catalog_service_creates_and_searches_named_catalogs(fake_uow_factory):
    service = CatalogService(fake_uow_factory)
    category = service.create_catalog(CreateCatalogCommand(CatalogType.CATEGORY, "Telefonia"))
    brand = service.create_catalog(CreateCatalogCommand(CatalogType.BRAND, "Acme"))

    assert category.name == "Telefonia"
    assert service.search_catalogs(CatalogType.BRAND, "acm")[0].id == brand.id


def test_service_and_package_keep_prices_and_duration(fake_uow_factory):
    service = CatalogService(fake_uow_factory)
    item = service.create_service(CreateServiceCommand("Troca de tela", Decimal("150"), 90, "Garantia 90 dias"))
    package = service.create_package(CreateServicePackageCommand("Revisão completa", ((item.id, 2),), Decimal("250")))

    assert item.price == Decimal("150.00")
    assert package.total == Decimal("250.00")
    assert package.items[0].quantity == Decimal("2")


def test_warranty_rule_rejects_negative_days(fake_uow_factory):
    service = CatalogService(fake_uow_factory)
    with pytest.raises(DomainValidationError):
        service.create_warranty_rule(CreateWarrantyRuleCommand("Garantia inválida", -1, "serviço"))
