from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas

from assistencia_manager.domain.entities.sales import Sale


class SalesReceiptService:
    def generate(self, sale: Sale, destination: Path, company: Mapping[str, str]) -> Path:
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        canvas = Canvas(str(destination), pagesize=A4)
        width, height = A4
        y = height - 48
        canvas.setTitle(f"Recibo de venda {sale.id}")
        canvas.setFont("Helvetica-Bold", 15)
        canvas.drawString(40, y, company.get("name", "Manutec"))
        y -= 22
        canvas.setFont("Helvetica", 10)
        if company.get("document"):
            canvas.drawString(40, y, f"Documento: {company['document']}")
            y -= 16
        canvas.setFont("Helvetica-Bold", 12)
        canvas.drawString(40, y, f"Recibo de venda {sale.id}")
        y -= 24
        canvas.setFont("Helvetica", 10)
        for item in sale.items:
            canvas.drawString(48, y, f"{item.description} ({item.quantity} x R$ {item.unit_price:.2f})")
            canvas.drawRightString(width - 40, y, f"R$ {item.amount:.2f}")
            y -= 16
        y -= 8
        canvas.drawString(40, y, f"Total: R$ {sale.total:.2f}")
        y -= 16
        canvas.drawString(40, y, f"Recebido: R$ {sale.paid_amount:.2f}")
        y -= 16
        canvas.drawString(40, y, f"Saldo: R$ {sale.remaining_amount:.2f}")
        canvas.save()
        return destination

    def generate_quote(self, sale: Sale, destination: Path, company: Mapping[str, str]) -> Path:
        """Gera o orçamento do carrinho sem exigir que a venda esteja concluída."""
        return self.generate(sale, destination, company)

    generate_budget = generate_quote
