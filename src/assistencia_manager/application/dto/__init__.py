"""Objetos de transporte entre interface, aplicação e domínio."""
from assistencia_manager.application.dto.client import CreateClientCommand, UpdateClientCommand
from assistencia_manager.application.dto.equipment import (
    CreateEquipmentCommand,
    UpdateEquipmentCommand,
)

__all__ = [
    "CreateClientCommand",
    "CreateEquipmentCommand",
    "UpdateClientCommand",
    "UpdateEquipmentCommand",
]
