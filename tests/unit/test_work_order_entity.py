from decimal import Decimal

import pytest

from assistencia_manager.domain.entities.work_order import WorkOrder, WorkOrderStatus
from assistencia_manager.domain.exceptions import DomainValidationError
from assistencia_manager.domain.identifiers import EntityId


def _order() -> WorkOrder:
    return WorkOrder.open(
        client_id=EntityId.new(),
        equipment_id=EntityId.new(),
        reported_issue="Não liga",
        intake_checklist=("Carcaça íntegra", "Acessórios recebidos"),
    )


def test_open_work_order_starts_open_with_initial_history():
    order = _order()

    assert order.status is WorkOrderStatus.OPEN
    assert order.reported_issue == "Não liga"
    assert order.history[0].event == "opened"


def test_work_order_accepts_only_declared_status_transitions():
    order = _order()

    order.transition_to(WorkOrderStatus.UNDER_ANALYSIS)
    order.transition_to(WorkOrderStatus.QUOTE_SENT)
    order.transition_to(WorkOrderStatus.APPROVED)
    order.transition_to(WorkOrderStatus.IN_PROGRESS)
    order.transition_to(WorkOrderStatus.COMPLETED)
    order.transition_to(WorkOrderStatus.DELIVERED)

    assert order.status is WorkOrderStatus.DELIVERED
    assert [item.event for item in order.history] == [
        "opened", "status_changed", "status_changed", "status_changed",
        "status_changed", "status_changed", "status_changed",
    ]


def test_work_order_rejects_invalid_status_jump_and_changes_after_delivery():
    order = _order()

    with pytest.raises(DomainValidationError):
        order.transition_to(WorkOrderStatus.APPROVED)

    order.transition_to(WorkOrderStatus.UNDER_ANALYSIS)
    order.transition_to(WorkOrderStatus.CANCELLED)
    with pytest.raises(DomainValidationError):
        order.add_item(description="Diagnóstico", quantity=1, unit_price=Decimal("10.00"))


def test_work_order_calculates_items_discount_and_total():
    order = _order()

    order.add_item(description="Serviço técnico", quantity=2, unit_price=Decimal("50.00"))
    order.add_item(description="Peça", quantity=1, unit_price=Decimal("30.00"), kind="part")
    order.set_discount(Decimal("10.00"))

    assert order.subtotal == Decimal("130.00")
    assert order.discount == Decimal("10.00")
    assert order.total == Decimal("120.00")
    assert len(order.history) == 4


def test_work_order_rejects_negative_money_and_zero_quantity():
    order = _order()

    with pytest.raises(DomainValidationError):
        order.add_item(description="Serviço", quantity=0, unit_price=Decimal("1.00"))
    with pytest.raises(DomainValidationError):
        order.set_discount(Decimal("-1.00"))


def test_work_order_history_is_read_only():
    order = _order()

    assert isinstance(order.history, tuple)
    with pytest.raises(AttributeError):
        order.history.append("tamper")
