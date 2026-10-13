from decimal import Decimal

import pytest

from assistencia_manager.domain.entities.sales import (
    CashRegister, Payment, PaymentMethod, PaymentStatus, Sale, SaleStatus,
)
from assistencia_manager.domain.exceptions import DomainValidationError
from assistencia_manager.domain.identifiers import EntityId


def test_sale_total_rounds_each_item_and_rejects_empty_sale_completion():
    sale = Sale.create()
    sale.add_item(description="Cabo", quantity="3", unit_price="10.005")

    assert sale.total == Decimal("30.03")
    sale.complete()
    with pytest.raises(DomainValidationError):
        Sale.create().complete()


def test_payment_can_be_reversed_once_and_preserves_original_amount():
    payment = Payment.record(
        sale_id=EntityId.new(), amount="10.005", method=PaymentMethod.PIX,
    )

    assert payment.amount == Decimal("10.01")
    payment.reverse()
    assert payment.status is PaymentStatus.REVERSED
    with pytest.raises(DomainValidationError):
        payment.reverse()


def test_cash_register_requires_open_before_movement_and_close():
    register = CashRegister.opening(amount="100.00")
    register.record(amount="25.00", description="Venda")
    register.close()

    assert register.balance == Decimal("125.00")
    assert register.is_open is False
    with pytest.raises(DomainValidationError):
        register.record(amount="1.00", description="Depois do fechamento")


def test_sale_tracks_paid_and_remaining_amount_and_rejects_overpayment():
    sale = Sale.create()
    sale.add_item(description="Cabo", quantity=1, unit_price="100")
    assert sale.paid_amount == Decimal("0.00")
    assert sale.remaining_amount == Decimal("100.00")
    sale.add_payment(Payment.record(sale_id=sale.id, amount="40", method=PaymentMethod.CASH))
    assert sale.paid_amount == Decimal("40.00")
    assert sale.remaining_amount == Decimal("60.00")
    with pytest.raises(DomainValidationError):
        sale.add_payment(Payment.record(sale_id=sale.id, amount="61", method=PaymentMethod.PIX))


def test_cash_register_supports_cash_in_and_out_without_losing_direction():
    register = CashRegister.opening(amount="100")
    register.record(amount="25", description="Sangria", movement_type="out")
    assert register.balance == Decimal("75.00")
