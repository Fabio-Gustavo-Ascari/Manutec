from __future__ import annotations

from typing import get_type_hints

from assistencia_manager.domain.repositories import ClientRepository, EquipmentRepository
from assistencia_manager.domain.unit_of_work import UnitOfWork


def test_repository_ports_are_framework_free_domain_contracts():
    assert ClientRepository.__module__.startswith("assistencia_manager.domain")
    assert EquipmentRepository.__module__.startswith("assistencia_manager.domain")
    assert UnitOfWork.__module__.startswith("assistencia_manager.domain")


def test_unit_of_work_exposes_client_and_equipment_repositories():
    annotations = get_type_hints(UnitOfWork)

    assert annotations["clients"] is ClientRepository
    assert annotations["equipment"] is EquipmentRepository
