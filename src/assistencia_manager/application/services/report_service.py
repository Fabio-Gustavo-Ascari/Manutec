from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from collections.abc import Callable, Iterable
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas

from assistencia_manager.domain.entities.work_order import WorkOrder
from assistencia_manager.domain.entities.procurement import PurchaseOrder


@dataclass(frozen=True, slots=True)
class ReportFilters:
    start: date | None = None
    end: date | None = None
    technician_id: str | None = None
    client_id: str | None = None
    status: str | None = None
    category: str | None = None
    search: str | None = None


@dataclass(frozen=True, slots=True)
class ReportResult:
    report_type: str
    columns: tuple[str, ...]
    rows: tuple[dict[str, object], ...]
    generated_at: datetime = field(default_factory=datetime.now)


def _safe(value: object) -> str:
    if isinstance(value, Decimal): text = f"{value:.2f}"
    elif isinstance(value, (datetime, date)): text = value.isoformat()
    else: text = "" if value is None else str(value)
    text = text.replace("\r", " ").replace("\n", " ").strip()
    return f"'{text}" if text[:1] in ("=", "+", "-", "@") else text


class ReportService:
    def __init__(self, unit_of_work_factory: Callable[[], object]) -> None:
        self._unit_of_work_factory = unit_of_work_factory

    def _items(self, name: str):
        with self._unit_of_work_factory() as uow:
            repository = getattr(uow, name, None)
            return tuple(repository.list()) if repository is not None else ()

    def generate(self, report_type: str, filters: ReportFilters | None = None) -> ReportResult:
        filters = filters or ReportFilters(); key = report_type.strip().lower().replace(" ", "_")
        builders = {"work_orders": self._work_orders, "orders": self._work_orders, "os": self._work_orders,
                    "sales": self._sales, "inventory": self._inventory, "stock": self._inventory,
                    "purchases": self._purchases, "purchase_orders": self._purchases, "finance": self._finance,
                    "financial": self._finance, "margin": self._margin, "productivity": self._productivity,
                    "technician_productivity": self._productivity, "warranties": self._warranties, "guarantees": self._warranties}
        if key not in builders: raise ValueError(f"Relatório desconhecido: {report_type}")
        return builders[key](filters)

    def _match(self, item, filters: ReportFilters, *, date_value=None) -> bool:
        status = getattr(getattr(item, "status", None), "value", getattr(item, "status", None))
        if filters.status and status != filters.status: return False
        for field_name in ("technician_id", "client_id"):
            expected = getattr(filters, field_name)
            if expected and str(getattr(item, field_name, "")) != str(expected): return False
        if filters.category and str(getattr(item, "category", "")) != filters.category: return False
        if filters.search and filters.search.casefold() not in " ".join(str(getattr(item, f, "")) for f in ("reported_issue", "description", "id")).casefold(): return False
        if date_value is not None:
            current = date_value.date() if isinstance(date_value, datetime) else date_value
            if filters.start and current < filters.start: return False
            if filters.end and current > filters.end: return False
        return True

    def _work_orders(self, filters):
        values = [i for i in self._items("work_orders") if self._match(i, filters, date_value=getattr(i, "due_at", None))]
        cols = ("id", "status", "client_id", "technician_id", "reported_issue", "due_at", "total", "warranty_until")
        return ReportResult("work_orders", cols, tuple({c: getattr(i, c, None) for c in cols} | {"total": i.total, "warranty_until": i.warranty_until} for i in values))

    def _sales(self, filters):
        values = [i for i in self._items("sales") if self._match(i, filters)]
        cols = ("id", "status", "client_id", "seller_id", "work_order_id", "total")
        return ReportResult("sales", cols, tuple({c: getattr(i, c, None) for c in cols} | {"total": i.total} for i in values))

    def _inventory(self, filters):
        values = [i for i in self._items("parts") if self._match(i, filters)]
        cols = ("id", "name", "sku", "category_id", "cost", "price", "minimum_stock", "active")
        return ReportResult("inventory", cols, tuple({c: getattr(i, c, None) for c in cols} for i in values))

    def _purchases(self, filters):
        values = [i for i in self._items("purchase_orders") if self._match(i, filters, date_value=getattr(i, "due_date", None))]
        cols = ("id", "supplier_id", "status", "due_date", "total")
        return ReportResult("purchases", cols, tuple({c: getattr(i, c, None) for c in cols} | {"total": i.total} for i in values))

    def _finance(self, filters):
        values = [i for i in self._items("financial_entries") if self._match(i, filters, date_value=getattr(i, "due_date", None))]
        cols = ("id", "entry_type", "description", "category", "due_date", "amount", "paid_amount", "status")
        return ReportResult("finance", cols, tuple({c: getattr(i, c, None) for c in cols} for i in values))

    def _margin(self, filters):
        rows = ({"id": r["id"], "revenue": r["total"], "cost": Decimal("0.00"), "margin": r["total"]} for r in self._sales(filters).rows)
        return ReportResult("margin", ("id", "revenue", "cost", "margin"), tuple(rows))

    def _productivity(self, filters):
        counts = {}
        for row in self._work_orders(filters).rows:
            key = str(row.get("technician_id") or "unassigned"); counts[key] = counts.get(key, 0) + 1
        return ReportResult("productivity", ("technician_id", "completed_orders"), tuple({"technician_id": k, "completed_orders": v} for k, v in counts.items()))

    def _warranties(self, filters):
        cols = ("id", "client_id", "technician_id", "warranty_until", "status")
        rows = [r for r in self._work_orders(filters).rows if r.get("warranty_until") is not None]
        return ReportResult("warranties", cols, tuple({c: r.get(c) for c in cols} for r in rows))

    def export_csv(self, result: ReportResult, destination: Path) -> Path:
        destination = Path(destination); destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream); writer.writerow(result.columns)
            for row in result.rows: writer.writerow([_safe(row.get(c)) for c in result.columns])
        return destination

    def export_pdf(self, result: ReportResult, destination: Path) -> Path:
        destination = Path(destination); destination.parent.mkdir(parents=True, exist_ok=True)
        canvas = Canvas(str(destination), pagesize=A4); _, height = A4; y = height - 40
        canvas.setTitle(f"Manutec - {result.report_type}"); canvas.drawString(40, y, f"Relatório: {result.report_type}"); y -= 24
        for row in result.rows:
            canvas.drawString(40, y, " | ".join(f"{c}: {_safe(row.get(c))}" for c in result.columns)[:150]); y -= 14
            if y < 40: canvas.showPage(); y = height - 40
        canvas.save(); return destination

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

    def purchase_orders(self, *, status: str | None = None) -> tuple[PurchaseOrder, ...]:
        with self._unit_of_work_factory() as uow:
            values = tuple(getattr(uow.purchase_orders, "list", lambda: ())())
        return tuple(order for order in values if not status or order.status.value == status)

    def export_purchase_orders_csv(self, orders: Iterable[PurchaseOrder], destination: Path) -> Path:
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(("id", "supplier_id", "status", "due_date", "total"))
            for order in orders:
                writer.writerow((str(order.id), str(order.supplier_id), order.status.value, order.due_date or "", f"{order.total:.2f}"))
        return destination
