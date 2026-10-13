from decimal import Decimal

import pytest

from assistencia_manager.domain.entities.sales import PaymentMethod, Sale
from assistencia_manager.domain.exceptions import DomainValidationError
from assistencia_manager.domain.identifiers import EntityId
from assistencia_manager.application.dto.inventory import CreatePartCommand, PartSearchQuery
from assistencia_manager.application.services.inventory_service import InventoryService
from assistencia_manager.bootstrap import initialize_database
from assistencia_manager.infrastructure.config.paths import AppPaths
from assistencia_manager.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork


def test_sale_2_supports_discount_editable_cart_and_change():
    sale = Sale.create(seller_id=EntityId.new(), quote_id=EntityId.new())
    sale.add_item(description="Cabo", quantity=2, unit_price="10", discount="3")
    assert sale.total == Decimal("17.00")
    sale.update_item(0, quantity=3, unit_price="12", discount="2")
    assert sale.total == Decimal("34.00")
    sale.remove_item(0)
    assert sale.total == Decimal("0.00")


def test_sale_2_accepts_debit_credit_and_cash_change_but_not_card_overpayment():
    sale = Sale.create()
    sale.add_item(description="Tela", quantity=1, unit_price="100")
    payment = sale.record_payment(amount="120", method=PaymentMethod.CASH)
    assert payment.amount == Decimal("120.00")
    assert sale.change == Decimal("20.00")

    other = Sale.create()
    other.add_item(description="Tela", quantity=1, unit_price="100")
    with pytest.raises(DomainValidationError):
        other.record_payment(amount="101", method=PaymentMethod.CREDIT)

    assert PaymentMethod.DEBIT.value == "debit"


def test_sale_2_validates_partial_payment_and_keeps_commercial_links():
    client, seller, quote, order = (EntityId.new() for _ in range(4))
    sale = Sale.create(client_id=client, seller_id=seller, quote_id=quote, work_order_id=order)
    sale.add_item(description="Serviço", quantity=1, unit_price="100")
    sale.record_payment(amount="40", method=PaymentMethod.DEBIT)
    assert sale.remaining_amount == Decimal("60.00")
    assert sale.seller_id == seller
    assert sale.quote_id == quote


def test_e13_part_search_matches_description_sku_and_barcode(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    engine = initialize_database(AppPaths.default())
    service = InventoryService(lambda: SqlAlchemyUnitOfWork(engine))
    service.create_part(CreatePartCommand("Tela IPS", "Telas", sku="TEL-001", barcode="789001", price=100))
    assert len(service.search(PartSearchQuery("ips")).items) == 1
    assert len(service.search(PartSearchQuery("TEL-001")).items) == 1
    assert len(service.search(PartSearchQuery("789001")).items) == 1
    engine.dispose()
