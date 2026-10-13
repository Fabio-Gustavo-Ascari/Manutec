"""Objetos de transporte entre interface, aplicação e domínio."""
from assistencia_manager.application.dto.client import (
    ClientSearchQuery,
    CreateClientCommand,
    UpdateClientCommand,
)
from assistencia_manager.application.dto.equipment import (
    CreateEquipmentCommand,
    EquipmentSearchQuery,
    UpdateEquipmentCommand,
)
from assistencia_manager.application.dto.pagination import Page

__all__ = [
    "CreateClientCommand",
    "CreateEquipmentCommand",
    "ClientSearchQuery",
    "EquipmentSearchQuery",
    "Page",
    "UpdateClientCommand",
    "UpdateEquipmentCommand",
]
