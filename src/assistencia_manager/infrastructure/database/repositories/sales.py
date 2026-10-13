from __future__ import annotations

from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session

from assistencia_manager.domain.entities.sales import (
    CashRegister, Payment, PaymentMethod, PaymentStatus, Sale, SaleItem, SaleStatus,
)
from assistencia_manager.domain.identifiers import EntityId
from assistencia_manager.infrastructure.database.models.sales import CashRegisterModel, PaymentModel, SaleModel


class SqlAlchemySaleRepository:
    def __init__(self, session: Session) -> None: self._session = session

    def add(self, entity: Sale) -> None:
        self._session.merge(SaleModel(
            id=str(entity.id), client_id=str(entity.client_id) if entity.client_id else None,
            work_order_id=str(entity.work_order_id) if entity.work_order_id else None,
            status=entity.status.value,
            items=[{"description": i.description, "quantity": str(i.quantity), "unit_price": str(i.unit_price), "part_id": str(i.part_id) if i.part_id else None} for i in entity.items],
        ))

    def get(self, identifier: EntityId) -> Sale | None:
        model = self._session.get(SaleModel, str(identifier))
        if not model: return None
        sale = self._to_entity(model)
        sale.payments = [SqlAlchemyPaymentRepository._to_entity(item) for item in self._session.scalars(select(PaymentModel).where(PaymentModel.sale_id == model.id))]
        return sale

    def list(self) -> tuple[Sale, ...]:
        return tuple(self.get(EntityId.from_str(model.id)) for model in self._session.scalars(select(SaleModel)))

    def remove(self, identifier: EntityId) -> None:
        model = self._session.get(SaleModel, str(identifier))
        if model: self._session.delete(model)

    def list_for_work_order(self, work_order_id: EntityId) -> tuple[Sale, ...]:
        return tuple(self.get(EntityId.from_str(model.id)) for model in self._session.scalars(select(SaleModel).where(SaleModel.work_order_id == str(work_order_id))))

    @staticmethod
    def _to_entity(model: SaleModel) -> Sale:
        sale = Sale(id=EntityId.from_str(model.id), client_id=EntityId.from_str(model.client_id) if model.client_id else None, work_order_id=EntityId.from_str(model.work_order_id) if model.work_order_id else None, status=SaleStatus(model.status), items=[])
        sale.items = [SaleItem(i["description"], Decimal(i["quantity"]), Decimal(i["unit_price"]), EntityId.from_str(i["part_id"]) if i.get("part_id") else None) for i in model.items or ()]
        return sale


class SqlAlchemyPaymentRepository:
    def __init__(self, session: Session) -> None: self._session = session

    def add(self, entity: Payment) -> None:
        self._session.merge(PaymentModel(id=str(entity.id), sale_id=str(entity.sale_id), amount=entity.amount, method=entity.method.value, installments=entity.installments, status=entity.status.value))

    def get(self, identifier: EntityId) -> Payment | None:
        model = self._session.get(PaymentModel, str(identifier))
        return self._to_entity(model) if model else None

    def list(self) -> tuple[Payment, ...]:
        return tuple(self._to_entity(model) for model in self._session.scalars(select(PaymentModel)))

    def remove(self, identifier: EntityId) -> None:
        raise NotImplementedError("Pagamentos são imutáveis; use estorno")

    def list_for_sale(self, sale_id: EntityId) -> tuple[Payment, ...]:
        return tuple(self._to_entity(model) for model in self._session.scalars(select(PaymentModel).where(PaymentModel.sale_id == str(sale_id))))

    @staticmethod
    def _to_entity(model: PaymentModel) -> Payment:
        return Payment(sale_id=EntityId.from_str(model.sale_id), amount=Decimal(str(model.amount)), method=PaymentMethod(model.method), installments=model.installments, status=PaymentStatus(model.status), id=EntityId.from_str(model.id))


class SqlAlchemyCashRegisterRepository:
    def __init__(self, session: Session) -> None: self._session = session

    def add(self, entity: CashRegister) -> None:
        self._session.merge(CashRegisterModel(id=str(entity.id), opening_amount=entity.opening_amount, movements=[{"amount": str(a), "type": t, "description": d} for a, t, d in entity.movements], is_open=entity.is_open))

    def get(self, identifier: EntityId) -> CashRegister | None:
        model = self._session.get(CashRegisterModel, str(identifier))
        if not model: return None
        return CashRegister(id=EntityId.from_str(model.id), opening_amount=Decimal(str(model.opening_amount)), movements=[(Decimal(m["amount"]), m["type"], m["description"]) for m in model.movements or ()], is_open=model.is_open)

    def list(self) -> tuple[CashRegister, ...]:
        return tuple(self.get(EntityId.from_str(model.id)) for model in self._session.scalars(select(CashRegisterModel)))

    def remove(self, identifier: EntityId) -> None: raise NotImplementedError("Caixas não são removidos")

    def current_open(self) -> CashRegister | None:
        model = self._session.scalar(select(CashRegisterModel).where(CashRegisterModel.is_open.is_(True)).order_by(CashRegisterModel.id.desc()))
        return self.get(EntityId.from_str(model.id)) if model else None
