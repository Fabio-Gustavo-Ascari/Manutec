from __future__ import annotations

import csv
from collections.abc import Callable, Iterable
from pathlib import Path

from assistencia_manager.domain.entities.work_order import WorkOrder


class ReportService:
    def __init__(self, unit_of_work_factory: Callable[[], object]) -> None:
        self._unit_of_work_factory = unit_of_work_factory

    def orders(self, *, status: str | None = None, search: str | None = None) -> tuple[WorkOrder, ...]:
        with self._unit_of_work_factory() as uow:
            values = tuple(uow.work_orders.list())
        return tuple(
            order for order in values
            if (not status or order.status.value == status)
            and (not search or search.casefold() in order.reported_issue.casefold())
        )

    def export_orders_csv(self, orders: Iterable[WorkOrder], destination: Path) -> Path:
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(("id", "status", "due_at", "total"))
            for order in orders:
                writer.writerow((str(order.id), order.status.value, order.due_at or "", f"{order.total:.2f}"))
        return destination
