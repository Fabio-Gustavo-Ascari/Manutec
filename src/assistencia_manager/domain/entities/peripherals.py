from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from assistencia_manager.domain.exceptions import DomainValidationError


class PrinterKind(Enum):
    THERMAL = "thermal"
    A4 = "a4"


@dataclass(frozen=True, slots=True)
class PeripheralResult:
    success: bool
    message: str
    reference: str | None = None


def validate_printer_name(name: str) -> str:
    normalized = name.strip()
    if not normalized:
        raise DomainValidationError("Nome da impressora é obrigatório")
    return normalized

