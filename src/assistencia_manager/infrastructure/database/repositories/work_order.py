from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from assistencia_manager.domain.entities.work_order import (
    WorkOrder, WorkOrderHistoryEntry, WorkOrderItem, WorkOrderStatus, WorkOrderPriority,
)
from assistencia_manager.domain.identifiers import EntityId
from assistencia_manager.infrastructure.database.models.work_order import WorkOrderModel


class SqlAlchemyWorkOrderRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, entity: WorkOrder) -> None:
        self._session.merge(WorkOrderModel(
            id=str(entity.id), status=entity.status.value, client_id=str(entity.client_id),
            equipment_id=str(entity.equipment_id), reported_issue=entity.reported_issue,
            intake_checklist=list(entity.intake_checklist), diagnosis=entity.diagnosis,
            notes=entity.notes,
            items=[{"description": i.description, "quantity": str(i.quantity), "unit_price": str(i.unit_price), "kind": i.kind, "part_id": str(i.part_id) if i.part_id else None} for i in entity.items],
            discount=entity.discount,
            history=[{"event": h.event, "description": h.description, "created_at": h.created_at.isoformat()} for h in entity.history],
            due_at=entity.due_at, priority=entity.priority.value,
            technician_id=str(entity.technician_id) if entity.technician_id else None,
            warranty_days=entity.warranty_days, origin=entity.origin, checklist=list(entity.checklist),
            observations=entity.observations, photos=list(entity.photos), attachments=list(entity.attachments),
            report=entity.report, delivered_at=entity.delivered_at,
        ))

    def get(self, identifier: EntityId) -> WorkOrder | None:
        model = self._session.get(WorkOrderModel, str(identifier))
        return self._to_entity(model) if model else None

    def list(self) -> tuple[WorkOrder, ...]:
        return tuple(self._to_entity(model) for model in self._session.scalars(select(WorkOrderModel)))

    def remove(self, identifier: EntityId) -> None:
        model = self._session.get(WorkOrderModel, str(identifier))
        if model is not None:
            self._session.delete(model)

    def search(self, term: str | None, status: str | None, offset: int, limit: int) -> tuple[WorkOrder, ...]:
        statement = select(WorkOrderModel)
        if status:
            statement = statement.where(WorkOrderModel.status == status)
        if term and term.strip():
            statement = statement.where(WorkOrderModel.reported_issue.ilike(f"%{term.strip()}%"))
        statement = statement.order_by(WorkOrderModel.id).offset(offset).limit(limit)
        return tuple(self._to_entity(model) for model in self._session.scalars(statement))

    def count(self, term: str | None, status: str | None) -> int:
        statement = select(WorkOrderModel.id)
        if status:
            statement = statement.where(WorkOrderModel.status == status)
        if term and term.strip():
            statement = statement.where(WorkOrderModel.reported_issue.ilike(f"%{term.strip()}%"))
        return self._session.scalar(select(func.count()).select_from(statement.subquery())) or 0

    @staticmethod
    def _to_entity(model: WorkOrderModel) -> WorkOrder:
        return WorkOrder(
            id=EntityId.from_str(model.id), status=WorkOrderStatus(model.status),
            client_id=EntityId.from_str(model.client_id), equipment_id=EntityId.from_str(model.equipment_id),
            reported_issue=model.reported_issue, intake_checklist=tuple(model.intake_checklist or ()),
            diagnosis=model.diagnosis, notes=model.notes,
            items=[WorkOrderItem(i["description"], Decimal(i["quantity"]), Decimal(i["unit_price"]), i["kind"], EntityId.from_str(i["part_id"]) if i.get("part_id") else None) for i in model.items or ()],
            discount=Decimal(str(model.discount)),
            history_entries=[WorkOrderHistoryEntry(h["event"], h["description"], datetime.fromisoformat(h["created_at"])) for h in model.history or ()],
            due_at=model.due_at, priority=WorkOrderPriority(model.priority or "normal"),
            technician_id=EntityId.from_str(model.technician_id) if model.technician_id else None,
            warranty_days=model.warranty_days or 0, origin=model.origin or "counter",
            checklist=tuple(model.checklist or ()), observations=model.observations,
            photos=tuple(model.photos or ()), attachments=tuple(model.attachments or ()),
            report=model.report, delivered_at=model.delivered_at,
        )
