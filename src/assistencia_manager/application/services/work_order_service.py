from __future__ import annotations

from collections.abc import Callable, Sequence

from assistencia_manager.application.dto.pagination import Page
from assistencia_manager.application.dto.work_order import (
    AddWorkOrderItemCommand,
    OpenWorkOrderCommand,
    WorkOrderSearchQuery,
    WorkOrderStatusCommand,
)
from assistencia_manager.domain.entities.work_order import WorkOrder
from assistencia_manager.domain.exceptions import EntityNotFoundError
from assistencia_manager.domain.unit_of_work import UnitOfWork


class WorkOrderService:
    def __init__(self, unit_of_work_factory: Callable[[], UnitOfWork]) -> None:
        self._unit_of_work_factory = unit_of_work_factory

    def open(self, command: OpenWorkOrderCommand) -> WorkOrder:
        with self._unit_of_work_factory() as uow:
            if uow.clients.get(command.client_id) is None:
                raise EntityNotFoundError(f"Cliente {command.client_id} não encontrado")
            if uow.equipment.get(command.equipment_id) is None:
                raise EntityNotFoundError(f"Equipamento {command.equipment_id} não encontrado")
            order = WorkOrder.open(
                client_id=command.client_id,
                equipment_id=command.equipment_id,
                reported_issue=command.reported_issue,
                intake_checklist=command.intake_checklist,
                notes=command.notes,
            )
            uow.work_orders.add(order)
            return order

    def add_item(self, command: AddWorkOrderItemCommand) -> WorkOrder:
        with self._unit_of_work_factory() as uow:
            order = self._get(uow, command.identifier)
            order.add_item(
                description=command.description,
                quantity=command.quantity,
                unit_price=command.unit_price,
                kind=command.kind,
            )
            uow.work_orders.add(order)
            return order

    def transition(self, command: WorkOrderStatusCommand) -> WorkOrder:
        with self._unit_of_work_factory() as uow:
            order = self._get(uow, command.identifier)
            order.transition_to(command.status)
            uow.work_orders.add(order)
            return order

    def get(self, identifier):
        with self._unit_of_work_factory() as uow:
            return self._get(uow, identifier)

    def list(self) -> Sequence[WorkOrder]:
        with self._unit_of_work_factory() as uow:
            return tuple(uow.work_orders.list())

    def search(self, query: WorkOrderSearchQuery) -> Page[WorkOrder]:
        with self._unit_of_work_factory() as uow:
            offset = (query.page - 1) * query.page_size
            status = query.status.value if query.status else None
            return Page(
                items=tuple(uow.work_orders.search(query.search, status, offset, query.page_size)),
                page=query.page,
                page_size=query.page_size,
                total_items=uow.work_orders.count(query.search, status),
            )

    @staticmethod
    def _get(uow: UnitOfWork, identifier):
        order = uow.work_orders.get(identifier)
        if order is None:
            raise EntityNotFoundError(f"Ordem {identifier} não encontrada")
        return order
