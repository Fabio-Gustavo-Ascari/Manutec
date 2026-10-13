from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from assistencia_manager.domain.entities.base import EntityStatus
from assistencia_manager.domain.entities.catalog import CatalogEntry, CatalogType, Service, ServiceItem, ServicePackage, WarrantyRule
from assistencia_manager.domain.identifiers import EntityId
from assistencia_manager.infrastructure.database.models.catalog import CatalogEntryModel, ServiceModel, ServicePackageModel, WarrantyRuleModel


class SqlAlchemyCatalogRepository:
    def __init__(self, session: Session): self._session = session
    def add(self, entity: CatalogEntry) -> None:
        self._session.merge(CatalogEntryModel(id=str(entity.id), kind=entity.kind.value, name=entity.name, document=entity.document, phone=entity.phone, email=entity.email, notes=entity.notes, status=entity.status.value))
    def get(self, identifier):
        row = self._session.get(CatalogEntryModel, str(identifier)); return self._to_entity(row) if row else None
    def list(self): return tuple(self._to_entity(x) for x in self._session.scalars(select(CatalogEntryModel)))
    def search(self, kind, term=None):
        q = select(CatalogEntryModel).where(CatalogEntryModel.kind == kind.value, CatalogEntryModel.status == EntityStatus.ACTIVE.value)
        if term and term.strip(): q = q.where(CatalogEntryModel.name.ilike(f"%{term.strip()}%"))
        return tuple(self._to_entity(x) for x in self._session.scalars(q.order_by(CatalogEntryModel.name)))
    def remove(self, identifier): raise NotImplementedError("Cadastros não podem ser removidos")
    @staticmethod
    def _to_entity(x): return CatalogEntry(id=EntityId.from_str(x.id), status=EntityStatus(x.status), kind=CatalogType(x.kind), name=x.name, document=x.document, phone=x.phone, email=x.email, notes=x.notes)


class SqlAlchemyServiceRepository:
    def __init__(self, session: Session): self._session = session
    def add(self, entity: Service) -> None: self._session.merge(ServiceModel(id=str(entity.id), name=entity.name, price=entity.price, warranty_days=entity.warranty_days, warranty_terms=entity.warranty_terms, description=entity.description, status=entity.status.value))
    def get(self, identifier):
        x = self._session.get(ServiceModel, str(identifier)); return self._to_entity(x) if x else None
    def list(self): return tuple(self._to_entity(x) for x in self._session.scalars(select(ServiceModel)))
    def remove(self, identifier): raise NotImplementedError("Serviços não podem ser removidos")
    @staticmethod
    def _to_entity(x): return Service(id=EntityId.from_str(x.id), status=EntityStatus(x.status), name=x.name, price=x.price, warranty_days=x.warranty_days, warranty_terms=x.warranty_terms, description=x.description)


class SqlAlchemyServicePackageRepository:
    def __init__(self, session: Session): self._session = session
    def add(self, entity: ServicePackage) -> None: self._session.merge(ServicePackageModel(id=str(entity.id), name=entity.name, items=[{"service_id": str(x.service_id), "quantity": str(x.quantity)} for x in entity.items], price=entity.price, status=entity.status.value))
    def get(self, identifier):
        x = self._session.get(ServicePackageModel, str(identifier)); return self._to_entity(x) if x else None
    def list(self): return tuple(self._to_entity(x) for x in self._session.scalars(select(ServicePackageModel)))
    def remove(self, identifier): raise NotImplementedError("Pacotes não podem ser removidos")
    @staticmethod
    def _to_entity(x): return ServicePackage(id=EntityId.from_str(x.id), status=EntityStatus(x.status), name=x.name, items=tuple(ServiceItem(EntityId.from_str(i["service_id"]), i["quantity"]) for i in x.items), price=x.price)


class SqlAlchemyWarrantyRuleRepository:
    def __init__(self, session: Session): self._session = session
    def add(self, entity: WarrantyRule) -> None: self._session.merge(WarrantyRuleModel(id=str(entity.id), name=entity.name, days=entity.days, applies_to=entity.applies_to, terms=entity.terms, status=entity.status.value))
    def get(self, identifier):
        x = self._session.get(WarrantyRuleModel, str(identifier)); return self._to_entity(x) if x else None
    def list(self): return tuple(self._to_entity(x) for x in self._session.scalars(select(WarrantyRuleModel)))
    def remove(self, identifier): raise NotImplementedError("Garantias não podem ser removidas")
    @staticmethod
    def _to_entity(x): return WarrantyRule(id=EntityId.from_str(x.id), status=EntityStatus(x.status), name=x.name, days=x.days, applies_to=x.applies_to, terms=x.terms)
