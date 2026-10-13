from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from assistencia_manager.domain.entities.work_order import WorkOrderStatus
from assistencia_manager.domain.exceptions import DomainValidationError
from assistencia_manager.domain.identifiers import EntityId


@dataclass(frozen=True, slots=True)
class OpenWorkOrderCommand:
    client_id: EntityId
    equipment_id: EntityId
    reported_issue: str
    intake_checklist: tuple[str, ...] = ()
    notes: str | None = None
    due_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class AddWorkOrderItemCommand:
    identifier: EntityId
    description: str
    quantity: Decimal
    unit_price: Decimal
    kind: str = "service"
    part_id: EntityId | None = None


@dataclass(frozen=True, slots=True)
class WorkOrderStatusCommand:
    identifier: EntityId
    status: WorkOrderStatus


@dataclass(frozen=True, slots=True)
class WorkOrderSearchQuery:
    search: str | None = None
    status: WorkOrderStatus | None = None
    page: int = 1
    page_size: int = 20

    def __post_init__(self) -> None:
        if self.page < 1:
            raise DomainValidationError("Página deve ser maior ou igual a 1")
        if not 1 <= self.page_size <= 100:
            raise DomainValidationError("Tamanho da página deve estar entre 1 e 100")

