"""Entidades e objetos persistentes do domínio Manutec."""
from assistencia_manager.domain.entities.client import Client
from assistencia_manager.domain.entities.base import Entity, EntityStatus
from assistencia_manager.domain.entities.equipment import Equipment

__all__ = ["Client", "Entity", "EntityStatus", "Equipment"]
from assistencia_manager.domain.entities.work_order import WorkOrder, WorkOrderItem, WorkOrderStatus

__all__ = ["WorkOrder", "WorkOrderItem", "WorkOrderStatus"]
