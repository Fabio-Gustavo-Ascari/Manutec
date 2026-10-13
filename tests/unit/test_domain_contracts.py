from uuid import UUID

import pytest

from assistencia_manager.domain.exceptions import DomainValidationError
from assistencia_manager.domain.identifiers import EntityId
from assistencia_manager.domain.repositories import Repository
from assistencia_manager.domain.unit_of_work import UnitOfWork


def test_entity_id_is_uuid_backed_and_can_be_recreated_from_text():
    identifier = EntityId.new()

    assert isinstance(identifier.value, UUID)
    assert EntityId.from_str(str(identifier)) == identifier


def test_entity_id_rejects_empty_or_invalid_values():
    with pytest.raises(DomainValidationError):
        EntityId.from_str("")

    with pytest.raises(DomainValidationError):
        EntityId.from_str("not-a-uuid")


def test_repository_and_unit_of_work_are_framework_free_contracts():
    assert Repository.__module__.startswith("assistencia_manager.domain")
    assert UnitOfWork.__module__.startswith("assistencia_manager.domain")

