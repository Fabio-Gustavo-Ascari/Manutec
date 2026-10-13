from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from assistencia_manager.domain.entities.base import EntityStatus
from assistencia_manager.domain.entities.inventory import (
    InventoryMovement, InventoryMovementType, Part, PartReservation, ReservationStatus,
)
from assistencia_manager.domain.identifiers import EntityId
from assistencia_manager.infrastructure.database.models.inventory import (
    InventoryMovementModel, PartModel, PartReservationModel,
)


class SqlAlchemyPartRepository:
    def __init__(self, session: Session) -> None: self._session = session

    def add(self, entity: Part) -> None:
        self._session.merge(PartModel(
            id=str(entity.id), name=entity.name, category=entity.category, unit=entity.unit,
            sku=entity.sku, cost=entity.cost, price=entity.price,
            minimum_stock=entity.minimum_stock, barcode=entity.barcode, brand=entity.brand,
            maximum_stock=entity.maximum_stock,
            supplier_id=str(entity.supplier_id) if entity.supplier_id else None, location=entity.location,
            warranty_days=entity.warranty_days, promotional_price=entity.promotional_price, status=entity.status.value,
        ))

    def get(self, identifier: EntityId) -> Part | None:
        model = self._session.get(PartModel, str(identifier))
        return self._to_entity(model) if model else None

    def list(self) -> tuple[Part, ...]:
        return tuple(self._to_entity(item) for item in self._session.scalars(select(PartModel)))

    def remove(self, identifier: EntityId) -> None:
        raise NotImplementedError("Peças não podem ser removidas; use inativação")

    def exists_by_sku(self, sku: str) -> bool:
        return self._session.scalar(select(func.count()).where(PartModel.sku == sku)) > 0

    def search(self, term: str | None, active_only: bool, offset: int, limit: int) -> tuple[Part, ...]:
        statement = select(PartModel)
        if active_only: statement = statement.where(PartModel.status == EntityStatus.ACTIVE.value)
        if term and term.strip():
            value = f"%{term.strip()}%"
            statement = statement.where(or_(PartModel.name.ilike(value), PartModel.sku.ilike(value), PartModel.barcode.ilike(value)))
        return tuple(self._to_entity(item) for item in self._session.scalars(statement.order_by(PartModel.name).offset(offset).limit(limit)))

    def count(self, term: str | None, active_only: bool) -> int:
        statement = select(PartModel.id)
        if active_only: statement = statement.where(PartModel.status == EntityStatus.ACTIVE.value)
        if term and term.strip():
            value = f"%{term.strip()}%"
            statement = statement.where(or_(PartModel.name.ilike(value), PartModel.sku.ilike(value), PartModel.barcode.ilike(value)))
        return self._session.scalar(select(func.count()).select_from(statement.subquery())) or 0

    @staticmethod
    def _to_entity(model: PartModel) -> Part:
        return Part(
            id=EntityId.from_str(model.id), status=EntityStatus(model.status), name=model.name,
            category=model.category, unit=model.unit, sku=model.sku,
            cost=Decimal(str(model.cost)), price=Decimal(str(model.price)),
            minimum_stock=Decimal(str(model.minimum_stock)),
            maximum_stock=Decimal(str(model.maximum_stock or 0)),
            barcode=model.barcode, brand=model.brand,
            supplier_id=EntityId.from_str(model.supplier_id) if model.supplier_id else None,
            location=model.location, warranty_days=model.warranty_days,
            promotional_price=Decimal(str(model.promotional_price)) if model.promotional_price is not None else None,
        )


class SqlAlchemyInventoryMovementRepository:
    def __init__(self, session: Session) -> None: self._session = session

    def add(self, entity: InventoryMovement) -> None:
        self._session.add(InventoryMovementModel(
            id=str(entity.id), part_id=str(entity.part_id), movement_type=entity.movement_type.value,
            quantity=entity.quantity, reference_id=str(entity.reference_id) if entity.reference_id else None,
            note=entity.note, created_at=entity.created_at,
        ))

    def list(self) -> tuple[InventoryMovement, ...]:
        return tuple(self._to_entity(item) for item in self._session.scalars(select(InventoryMovementModel).order_by(InventoryMovementModel.created_at)))

    def list_for_part(self, part_id: EntityId) -> tuple[InventoryMovement, ...]:
        statement = select(InventoryMovementModel).where(InventoryMovementModel.part_id == str(part_id)).order_by(InventoryMovementModel.created_at)
        return tuple(self._to_entity(item) for item in self._session.scalars(statement))

    @staticmethod
    def _to_entity(model: InventoryMovementModel) -> InventoryMovement:
        return InventoryMovement(
            id=EntityId.from_str(model.id), part_id=EntityId.from_str(model.part_id),
            movement_type=InventoryMovementType(model.movement_type), quantity=Decimal(str(model.quantity)),
            reference_id=EntityId.from_str(model.reference_id) if model.reference_id else None,
            note=model.note, created_at=model.created_at,
        )


class SqlAlchemyPartReservationRepository:
    def __init__(self, session: Session) -> None: self._session = session

    def add(self, entity: PartReservation) -> None:
        self._session.merge(PartReservationModel(
            id=str(entity.id), part_id=str(entity.part_id), work_order_id=str(entity.work_order_id),
            quantity=entity.quantity, status=entity.status.value, created_at=entity.created_at,
        ))

    def get(self, identifier: EntityId) -> PartReservation | None:
        model = self._session.get(PartReservationModel, str(identifier))
        return self._to_entity(model) if model else None

    def list_for_part(self, part_id: EntityId, active_only: bool = False) -> tuple[PartReservation, ...]:
        statement = select(PartReservationModel).where(PartReservationModel.part_id == str(part_id))
        if active_only: statement = statement.where(PartReservationModel.status == ReservationStatus.ACTIVE.value)
        return tuple(self._to_entity(item) for item in self._session.scalars(statement))

    def list_for_work_order(self, work_order_id: EntityId, active_only: bool = False) -> tuple[PartReservation, ...]:
        statement = select(PartReservationModel).where(PartReservationModel.work_order_id == str(work_order_id))
        if active_only: statement = statement.where(PartReservationModel.status == ReservationStatus.ACTIVE.value)
        return tuple(self._to_entity(item) for item in self._session.scalars(statement))

    @staticmethod
    def _to_entity(model: PartReservationModel) -> PartReservation:
        return PartReservation(
            id=EntityId.from_str(model.id), part_id=EntityId.from_str(model.part_id),
            work_order_id=EntityId.from_str(model.work_order_id), quantity=Decimal(str(model.quantity)),
            status=ReservationStatus(model.status), created_at=model.created_at,
        )
