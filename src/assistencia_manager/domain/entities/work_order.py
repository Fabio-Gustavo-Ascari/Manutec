from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum

from assistencia_manager.domain.entities.base import Entity
from assistencia_manager.domain.exceptions import DomainValidationError
from assistencia_manager.domain.identifiers import EntityId

MONEY = Decimal("0.01")


class WorkOrderStatus(Enum):
    OPEN = "open"
    UNDER_ANALYSIS = "under_analysis"
    QUOTE_SENT = "quote_sent"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


@dataclass(frozen=True, slots=True)
class WorkOrderItem:
    description: str
    quantity: Decimal
    unit_price: Decimal
    kind: str = "service"
    part_id: EntityId | None = None

    @property
    def amount(self) -> Decimal:
        return (self.quantity * self.unit_price).quantize(MONEY, rounding=ROUND_HALF_UP)


@dataclass(frozen=True, slots=True)
class WorkOrderHistoryEntry:
    event: str
    description: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


def _text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise DomainValidationError(f"{name} não pode ser vazio")
    return value.strip()


def _money(value: Decimal | int | str, name: str) -> Decimal:
    try:
        result = Decimal(str(value)).quantize(MONEY, rounding=ROUND_HALF_UP)
    except Exception as error:
        raise DomainValidationError(f"{name} deve ser um valor monetário válido") from error
    if result < 0:
        raise DomainValidationError(f"{name} não pode ser negativo")
    return result


def _quantity(value: Decimal | int | str) -> Decimal:
    try:
        result = Decimal(str(value))
    except Exception as error:
        raise DomainValidationError("Quantidade deve ser válida") from error
    if result <= 0:
        raise DomainValidationError("Quantidade deve ser maior que zero")
    return result


@dataclass(eq=False, slots=True)
class WorkOrder(Entity):
    client_id: EntityId | None = None
    equipment_id: EntityId | None = None
    status: WorkOrderStatus = WorkOrderStatus.OPEN
    reported_issue: str = ""
    intake_checklist: tuple[str, ...] = field(default_factory=tuple)
    diagnosis: str | None = None
    notes: str | None = None
    items: list[WorkOrderItem] = field(default_factory=list)
    discount: Decimal = Decimal("0.00")
    history_entries: list[WorkOrderHistoryEntry] = field(default_factory=list, repr=False)
    due_at: datetime | None = None

    @property
    def history(self) -> tuple[WorkOrderHistoryEntry, ...]:
        return tuple(self.history_entries)

    @classmethod
    def open(
        cls,
        *,
        client_id: EntityId,
        equipment_id: EntityId,
        reported_issue: str,
        intake_checklist: tuple[str, ...] = (),
        notes: str | None = None,
        due_at: datetime | None = None,
    ) -> WorkOrder:
        if not isinstance(client_id, EntityId) or not isinstance(equipment_id, EntityId):
            raise DomainValidationError("Ordem deve possuir cliente e equipamento válidos")
        order = cls(
            client_id=client_id,
            equipment_id=equipment_id,
            reported_issue=_text(reported_issue, "Defeito relatado"),
            intake_checklist=tuple(item.strip() for item in intake_checklist if item.strip()),
            notes=notes.strip() if isinstance(notes, str) and notes.strip() else None,
            due_at=due_at,
        )
        order._record("opened", "Ordem de serviço aberta")
        return order

    def __post_init__(self) -> None:
        if not isinstance(self.client_id, EntityId) or not isinstance(self.equipment_id, EntityId):
            raise DomainValidationError("Ordem deve possuir cliente e equipamento válidos")
        self.reported_issue = _text(self.reported_issue, "Defeito relatado")
        self.discount = _money(self.discount, "Desconto")

    @property
    def subtotal(self) -> Decimal:
        return sum((item.amount for item in self.items), Decimal("0.00")).quantize(MONEY)

    @property
    def total(self) -> Decimal:
        return max(Decimal("0.00"), self.subtotal - self.discount).quantize(MONEY)

    def _ensure_editable(self) -> None:
        if self.status in {WorkOrderStatus.DELIVERED, WorkOrderStatus.REJECTED, WorkOrderStatus.CANCELLED}:
            raise DomainValidationError("Ordem encerrada não pode ser alterada")

    def _record(self, event: str, description: str) -> None:
        self.history_entries.append(WorkOrderHistoryEntry(event=event, description=description))

    def transition_to(self, target: WorkOrderStatus) -> None:
        allowed = {
            WorkOrderStatus.OPEN: {WorkOrderStatus.UNDER_ANALYSIS, WorkOrderStatus.CANCELLED},
            WorkOrderStatus.UNDER_ANALYSIS: {WorkOrderStatus.QUOTE_SENT, WorkOrderStatus.CANCELLED},
            WorkOrderStatus.QUOTE_SENT: {WorkOrderStatus.APPROVED, WorkOrderStatus.REJECTED, WorkOrderStatus.CANCELLED},
            WorkOrderStatus.APPROVED: {WorkOrderStatus.IN_PROGRESS, WorkOrderStatus.CANCELLED},
            WorkOrderStatus.IN_PROGRESS: {WorkOrderStatus.COMPLETED, WorkOrderStatus.CANCELLED},
            WorkOrderStatus.COMPLETED: {WorkOrderStatus.DELIVERED},
            WorkOrderStatus.REJECTED: set(),
            WorkOrderStatus.DELIVERED: set(),
            WorkOrderStatus.CANCELLED: set(),
        }
        if target not in allowed[self.status]:
            raise DomainValidationError(f"Transição inválida: {self.status.value} -> {target.value}")
        previous = self.status
        self.status = target
        self._record("status_changed", f"Status alterado de {previous.value} para {target.value}")

    def add_item(self, *, description: str, quantity: Decimal | int | str, unit_price: Decimal | int | str, kind: str = "service", part_id: EntityId | None = None) -> None:
        self._ensure_editable()
        kind = _text(kind, "Tipo do item")
        if kind not in {"service", "part"}:
            raise DomainValidationError("Tipo do item deve ser service ou part")
        if part_id is not None and not isinstance(part_id, EntityId):
            raise DomainValidationError("Peça do item deve ser válida")
        item = WorkOrderItem(_text(description, "Descrição"), _quantity(quantity), _money(unit_price, "Valor unitário"), kind)
        if part_id is not None:
            item = WorkOrderItem(item.description, item.quantity, item.unit_price, item.kind, part_id)
        self.items.append(item)
        self._record("item_added", f"Item adicionado: {item.description}")

    def set_diagnosis(self, diagnosis: str) -> None:
        self._ensure_editable()
        self.diagnosis = _text(diagnosis, "Diagnóstico")
        self._record("diagnosis_updated", "Diagnóstico atualizado")

    def set_discount(self, discount: Decimal | int | str) -> None:
        self._ensure_editable()
        self.discount = _money(discount, "Desconto")
        if self.discount > self.subtotal:
            raise DomainValidationError("Desconto não pode superar o subtotal")
        self._record("discount_updated", "Desconto atualizado")
