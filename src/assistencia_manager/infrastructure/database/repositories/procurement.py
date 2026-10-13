from sqlalchemy import select
from assistencia_manager.domain.entities.procurement import PurchaseOrder, PurchaseOrderLine, PurchaseOrderStatus
from assistencia_manager.domain.identifiers import EntityId
from assistencia_manager.infrastructure.database.models.procurement import PurchaseOrderLineModel, PurchaseOrderModel

class SqlAlchemyPurchaseOrderRepository:
    def __init__(self, session): self._session = session
    def add(self, entity: PurchaseOrder) -> None:
        self._session.merge(PurchaseOrderModel(id=str(entity.id), supplier_id=str(entity.supplier_id), status=entity.status.value, due_date=entity.due_date, notes=entity.notes, created_at=entity.created_at))
        self._session.flush()
        self._session.query(PurchaseOrderLineModel).filter(PurchaseOrderLineModel.purchase_order_id == str(entity.id)).delete(synchronize_session=False)
        for line in entity.lines:
            self._session.add(PurchaseOrderLineModel(id=str(EntityId.new()), purchase_order_id=str(entity.id), part_id=str(line.part_id), ordered_quantity=line.ordered_quantity, received_quantity=line.received_quantity, unit_cost=line.unit_cost))
    def get(self, identifier):
        model = self._session.get(PurchaseOrderModel, str(identifier))
        if model is None: return None
        lines = tuple(PurchaseOrderLine(EntityId.from_str(row.part_id), row.ordered_quantity, row.unit_cost, row.received_quantity) for row in self._session.scalars(select(PurchaseOrderLineModel).where(PurchaseOrderLineModel.purchase_order_id == str(identifier))))
        return PurchaseOrder(supplier_id=EntityId.from_str(model.supplier_id), lines=lines, due_date=model.due_date, notes=model.notes, status=PurchaseOrderStatus(model.status), id=EntityId.from_str(model.id), created_at=model.created_at)
    def list(self): return tuple(self.get(model.id) for model in self._session.scalars(select(PurchaseOrderModel).order_by(PurchaseOrderModel.created_at)))
    def list_open(self): return tuple(item for item in self.list() if item.status not in {PurchaseOrderStatus.RECEIVED, PurchaseOrderStatus.CANCELLED})
