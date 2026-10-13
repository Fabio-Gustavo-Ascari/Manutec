from decimal import Decimal

import pytest

from assistencia_manager.domain.entities.inventory import (
    InventoryMovementType,
    Part,
    PartReservation,
    ReservationStatus,
    StockLedger,
)
from assistencia_manager.domain.exceptions import DomainValidationError
from assistencia_manager.domain.identifiers import EntityId


def test_part_normalizes_catalog_data_and_rejects_negative_values():
    part = Part.create(
        name="  Tela LCD ", category="  Displays ", unit="un",
        sku=" lcd-01 ", cost="100", price="180", minimum_stock="2",
    )

    assert part.name == "Tela LCD"
    assert part.category == "Displays"
    assert part.sku == "LCD-01"
    assert part.cost == Decimal("100.00")
    assert part.minimum_stock == Decimal("2")

    with pytest.raises(DomainValidationError):
        Part.create(name="Cabo", category="Acessórios", unit="un", cost=-1, price=2)
    with pytest.raises(DomainValidationError):
        Part.create(name="Cabo", category="Acessórios", unit="un", cost=1, price=2, minimum_stock="x")


def test_ledger_derives_physical_and_available_balance_from_movements_and_reservations():
    part = Part.create(name="Cabo", category="Acessórios", unit="un", cost=2, price=5)
    ledger = StockLedger()
    ledger.record(part_id=part.id, movement_type=InventoryMovementType.ENTRY, quantity=10)
    ledger.record(part_id=part.id, movement_type=InventoryMovementType.EXIT, quantity=2)
    reservation = PartReservation.reserve(part_id=part.id, work_order_id=EntityId.new(), quantity=3)

    assert ledger.physical_balance(part.id) == Decimal("8")
    assert ledger.available_balance(part.id, (reservation,)) == Decimal("5")

    with pytest.raises(DomainValidationError):
        ledger.record(part_id=part.id, movement_type=InventoryMovementType.EXIT, quantity=9)


def test_reservation_can_be_released_once_or_converted_to_consumption_once():
    part_id = EntityId.new()
    order_id = EntityId.new()
    reservation = PartReservation.reserve(part_id=part_id, work_order_id=order_id, quantity=2)

    reservation.release()
    assert reservation.status is ReservationStatus.RELEASED
    with pytest.raises(DomainValidationError):
        reservation.release()

    consumed = PartReservation.reserve(part_id=part_id, work_order_id=order_id, quantity=1)
    consumed.consume()
    assert consumed.status is ReservationStatus.CONSUMED
    with pytest.raises(DomainValidationError):
        consumed.consume()
