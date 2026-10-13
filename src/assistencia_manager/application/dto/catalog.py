from dataclasses import dataclass
from decimal import Decimal

from assistencia_manager.domain.entities.catalog import CatalogType
from assistencia_manager.domain.identifiers import EntityId


@dataclass(frozen=True, slots=True)
class CreateCatalogCommand:
    kind: CatalogType
    name: str
    document: str | None = None
    phone: str | None = None
    email: str | None = None
    notes: str | None = None


@dataclass(frozen=True, slots=True)
class CreateServiceCommand:
    name: str
    price: Decimal
    warranty_days: int = 0
    warranty_terms: str | None = None
    description: str | None = None


@dataclass(frozen=True, slots=True)
class CreateServicePackageCommand:
    name: str
    items: tuple[tuple[EntityId, Decimal], ...]
    price: Decimal


@dataclass(frozen=True, slots=True)
class CreateWarrantyRuleCommand:
    name: str
    days: int
    applies_to: str
    terms: str | None = None
