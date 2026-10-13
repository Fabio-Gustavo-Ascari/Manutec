from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum

from assistencia_manager.domain.entities.base import Entity
from assistencia_manager.domain.exceptions import DomainValidationError
from assistencia_manager.domain.identifiers import EntityId


def _text(value: str, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DomainValidationError(f"{label} não pode ser vazio")
    return value.strip()


def _money(value: Decimal | int | str, label: str = "Preço") -> Decimal:
    try:
        result = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except Exception as error:
        raise DomainValidationError(f"{label} inválido") from error
    if result < 0:
        raise DomainValidationError(f"{label} não pode ser negativo")
    return result


class CatalogType(Enum):
    CATEGORY = "category"
    BRAND = "brand"
    SUPPLIER = "supplier"
    TECHNICIAN = "technician"


@dataclass(eq=False, slots=True)
class CatalogEntry(Entity):
    kind: CatalogType = CatalogType.CATEGORY
    name: str = ""
    document: str | None = None
    phone: str | None = None
    email: str | None = None
    notes: str | None = None

    @classmethod
    def create(cls, *, kind: CatalogType, name: str, document: str | None = None,
               phone: str | None = None, email: str | None = None, notes: str | None = None) -> "CatalogEntry":
        return cls(kind=kind, name=_text(name, "Nome"), document=document.strip() if document else None,
                   phone=phone.strip() if phone else None, email=email.strip() if email else None,
                   notes=notes.strip() if notes else None)

    def __post_init__(self) -> None:
        self.name = _text(self.name, "Nome")


@dataclass(frozen=True, slots=True)
class ServiceItem:
    service_id: EntityId
    quantity: Decimal

    def __post_init__(self) -> None:
        try:
            value = Decimal(str(self.quantity))
        except Exception as error:
            raise DomainValidationError("Quantidade de serviço inválida") from error
        if value <= 0:
            raise DomainValidationError("Quantidade de serviço deve ser maior que zero")
        object.__setattr__(self, "quantity", value)


@dataclass(eq=False, slots=True)
class Service(Entity):
    name: str = ""
    price: Decimal = Decimal("0.00")
    warranty_days: int = 0
    warranty_terms: str | None = None
    description: str | None = None

    @classmethod
    def create(cls, *, name: str, price: Decimal | int | str, warranty_days: int = 0,
               warranty_terms: str | None = None, description: str | None = None) -> "Service":
        return cls(name=_text(name, "Nome do serviço"), price=_money(price), warranty_days=warranty_days,
                   warranty_terms=warranty_terms.strip() if warranty_terms else None,
                   description=description.strip() if description else None)

    def __post_init__(self) -> None:
        self.name = _text(self.name, "Nome do serviço")
        self.price = _money(self.price)
        if self.warranty_days < 0:
            raise DomainValidationError("Garantia não pode ser negativa")


@dataclass(eq=False, slots=True)
class ServicePackage(Entity):
    name: str = ""
    items: tuple[ServiceItem, ...] = ()
    price: Decimal = Decimal("0.00")

    @classmethod
    def create(cls, *, name: str, items: tuple[ServiceItem, ...], price: Decimal | int | str) -> "ServicePackage":
        if not items:
            raise DomainValidationError("Pacote deve possuir ao menos um serviço")
        return cls(name=_text(name, "Nome do pacote"), items=tuple(items), price=_money(price))

    def __post_init__(self) -> None:
        self.name = _text(self.name, "Nome do pacote")
        self.price = _money(self.price)

    @property
    def total(self) -> Decimal:
        return self.price


@dataclass(eq=False, slots=True)
class WarrantyRule(Entity):
    name: str = ""
    days: int = 0
    applies_to: str = ""
    terms: str | None = None

    @classmethod
    def create(cls, *, name: str, days: int, applies_to: str, terms: str | None = None) -> "WarrantyRule":
        if days < 0:
            raise DomainValidationError("Dias de garantia não podem ser negativos")
        return cls(name=_text(name, "Nome da garantia"), days=days, applies_to=_text(applies_to, "Aplicação"), terms=terms)

    def __post_init__(self) -> None:
        self.name = _text(self.name, "Nome da garantia")
        self.applies_to = _text(self.applies_to, "Aplicação")
        if self.days < 0:
            raise DomainValidationError("Dias de garantia não podem ser negativos")
