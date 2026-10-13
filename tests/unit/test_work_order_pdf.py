from decimal import Decimal

from assistencia_manager.application.services.work_order_pdf import WorkOrderPdfService
from assistencia_manager.domain.entities.work_order import WorkOrder
from assistencia_manager.domain.identifiers import EntityId


def test_pdf_is_generated_from_company_order_and_total(tmp_path):
    order = WorkOrder.open(client_id=EntityId.new(), equipment_id=EntityId.new(), reported_issue="Não liga")
    order.add_item(description="Serviço técnico", quantity=1, unit_price=Decimal("150.00"))
    output = WorkOrderPdfService().generate(order, tmp_path / "orcamento.pdf", {"name": "Oficina Central", "document": "123"})

    content = output.read_bytes()
    assert content.startswith(b"%PDF-")
    assert len(content) > 1000
