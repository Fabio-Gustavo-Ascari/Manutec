from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas

from assistencia_manager.domain.entities.work_order import WorkOrder


class WorkOrderPdfService:
    def generate(self, order: WorkOrder, destination: Path, company: Mapping[str, str]) -> Path:
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        canvas = Canvas(str(destination), pagesize=A4)
        width, height = A4
        y = height - 48
        canvas.setTitle(f"Orçamento OS {order.id}")
        canvas.setFont("Helvetica-Bold", 15)
        canvas.drawString(40, y, company.get("name", "Manutec"))
        y -= 22
        canvas.setFont("Helvetica", 10)
        if company.get("document"):
            canvas.drawString(40, y, f"Documento: {company['document']}")
            y -= 16
        canvas.setFont("Helvetica-Bold", 12)
        canvas.drawString(40, y, f"Orçamento / Ordem de serviço {order.id}")
        y -= 24
        canvas.setFont("Helvetica", 10)
        canvas.drawString(40, y, f"Status: {order.status.value}")
        y -= 16
        canvas.drawString(40, y, f"Defeito relatado: {order.reported_issue}")
        y -= 24
        for item in order.items:
            canvas.drawString(48, y, f"{item.description} ({item.quantity} x R$ {item.unit_price:.2f})")
            canvas.drawRightString(width - 40, y, f"R$ {item.amount:.2f}")
            y -= 16
        y -= 8
        canvas.drawString(40, y, f"Subtotal: R$ {order.subtotal:.2f}")
        y -= 16
        canvas.drawString(40, y, f"Desconto: R$ {order.discount:.2f}")
        y -= 18
        canvas.setFont("Helvetica-Bold", 11)
        canvas.drawString(40, y, f"Total: R$ {order.total:.2f}")
        canvas.save()
        return destination

    def generate_document(self, order: WorkOrder, destination: Path, company: Mapping[str, str], kind: str) -> Path:
        labels = {"quote": "Orçamento", "report": "Laudo técnico", "intake": "Comprovante de entrada", "delivery": "Termo de entrega"}
        if kind not in labels:
            raise ValueError("Tipo de documento inválido")
        destination = Path(destination); destination.parent.mkdir(parents=True, exist_ok=True)
        canvas = Canvas(str(destination), pagesize=A4); _, height = A4; y = height - 48
        canvas.setTitle(f"{labels[kind]} OS {order.id}"); canvas.setFont("Helvetica-Bold", 15)
        canvas.drawString(40, y, company.get("name", "Manutec")); y -= 28
        canvas.setFont("Helvetica-Bold", 13); canvas.drawString(40, y, f"{labels[kind]} — OS {order.id}"); y -= 24
        canvas.setFont("Helvetica", 10)
        for line in (f"Status: {order.status.value}", f"Origem: {order.origin}", f"Prioridade: {order.priority.value}", f"Defeito: {order.reported_issue}"):
            canvas.drawString(40, y, line); y -= 16
        if kind == "report":
            y -= 8; canvas.drawString(40, y, f"Diagnóstico: {order.diagnosis or 'Não informado'}"); y -= 18
            canvas.drawString(40, y, f"Laudo: {order.report or 'Não informado'}"); y -= 18
        if kind == "delivery":
            canvas.drawString(40, y, f"Total: R$ {order.total:.2f}"); y -= 18
            canvas.drawString(40, y, f"Garantia: {order.warranty_days} dias"); y -= 18
        if kind == "quote":
            canvas.drawString(40, y, f"Total do orçamento: R$ {order.total:.2f}"); y -= 18
        if kind == "intake":
            canvas.drawString(40, y, f"Checklist: {', '.join(order.checklist or order.intake_checklist) or 'Nenhum'}"); y -= 18
        canvas.drawString(40, y, "Documento emitido pelo Manutec."); canvas.save(); return destination
