from __future__ import annotations

from collections.abc import Callable, Sequence

from assistencia_manager.application.dto.catalog import (
    CreateCatalogCommand, CreateServiceCommand, CreateServicePackageCommand, CreateWarrantyRuleCommand,
)
from assistencia_manager.domain.entities.catalog import CatalogEntry, CatalogType, Service, ServiceItem, ServicePackage, WarrantyRule
from assistencia_manager.domain.exceptions import DuplicateEntityError, EntityNotFoundError


class CatalogService:
    def __init__(self, unit_of_work_factory: Callable[[], object]) -> None:
        self._factory = unit_of_work_factory

    def create_catalog(self, command: CreateCatalogCommand) -> CatalogEntry:
        with self._factory() as uow:
            if any(x.kind is command.kind and x.name.casefold() == command.name.strip().casefold() for x in uow.catalogs.list()):
                raise DuplicateEntityError(f"{command.name} já cadastrado")
            value = CatalogEntry.create(**command.__dict__) if hasattr(command, "__dict__") else CatalogEntry.create(
                kind=command.kind, name=command.name, document=command.document, phone=command.phone,
                email=command.email, notes=command.notes)
            uow.catalogs.add(value)
            return value

    def search_catalogs(self, kind: CatalogType, term: str | None = None) -> Sequence[CatalogEntry]:
        with self._factory() as uow:
            return uow.catalogs.search(kind, term)

    def create_service(self, command: CreateServiceCommand) -> Service:
        with self._factory() as uow:
            value = Service.create(name=command.name, price=command.price, warranty_days=command.warranty_days,
                                   warranty_terms=command.warranty_terms, description=command.description)
            uow.services.add(value)
            return value

    def create_package(self, command: CreateServicePackageCommand) -> ServicePackage:
        with self._factory() as uow:
            items = []
            for service_id, quantity in command.items:
                if uow.services.get(service_id) is None:
                    raise EntityNotFoundError(f"Serviço {service_id} não encontrado")
                items.append(ServiceItem(service_id, quantity))
            value = ServicePackage.create(name=command.name, items=tuple(items), price=command.price)
            uow.service_packages.add(value)
            return value

    def create_warranty_rule(self, command: CreateWarrantyRuleCommand) -> WarrantyRule:
        with self._factory() as uow:
            value = WarrantyRule.create(name=command.name, days=command.days, applies_to=command.applies_to, terms=command.terms)
            uow.warranty_rules.add(value)
            return value
