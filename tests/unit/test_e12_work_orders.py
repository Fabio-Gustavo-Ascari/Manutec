from datetime import datetime, timezone
from decimal import Decimal

from assistencia_manager.domain.entities.work_order import WorkOrder, WorkOrderPriority
from assistencia_manager.domain.identifiers import EntityId


def test_work_order_2_0_keeps_service_metadata_and_operational_evidence():
    technician = EntityId.new()
    order = WorkOrder.open(
        client_id=EntityId.new(), equipment_id=EntityId.new(), reported_issue="Tela apagada",
        priority=WorkOrderPriority.HIGH, technician_id=technician, origin="whatsapp",
        warranty_days=90, checklist=("Lacre", "Carregador"), due_at=datetime.now(timezone.utc),
    )
    order.set_diagnosis("Conector oxidado")
    order.set_observations("Cliente autorizou limpeza")
    order.add_photo("fotos/entrada-01.jpg")
    order.add_attachment("laudo-assinado.pdf")
    order.set_report("Laudo técnico final")

    assert order.priority is WorkOrderPriority.HIGH
    assert order.technician_id == technician
    assert order.origin == "whatsapp"
    assert order.warranty_days == 90
    assert order.checklist == ("Lacre", "Carregador")
    assert order.photos == ("fotos/entrada-01.jpg",)
    assert order.attachments == ("laudo-assinado.pdf",)
    assert order.report == "Laudo técnico final"

