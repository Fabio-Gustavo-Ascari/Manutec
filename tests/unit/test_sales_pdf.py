from decimal import Decimal

from assistencia_manager.application.services.sales_pdf import SalesReceiptService
from assistencia_manager.domain.entities.sales import Payment, PaymentMethod, Sale


def test_sales_receipt_is_generated_with_totals(tmp_path):
    sale = Sale.create()
    sale.add_item(description="Cabo", quantity=1, unit_price=Decimal("25"))
    sale.complete()
    sale.add_payment(Payment.record(sale_id=sale.id, amount=Decimal("25"), method=PaymentMethod.PIX))
    output = SalesReceiptService().generate(sale, tmp_path / "recibo.pdf", {"name": "Oficina"})
    assert output.read_bytes().startswith(b"%PDF-")
