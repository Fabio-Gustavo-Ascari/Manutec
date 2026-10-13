import pytest

from assistencia_manager.domain.entities.base import Entity, EntityStatus
from assistencia_manager.domain.exceptions import InactiveEntityError
from assistencia_manager.domain.identifiers import EntityId


def test_entity_has_an_identity_and_compares_by_type_and_id():
    identifier = EntityId.new()
    first = Entity(identifier)
    second = Entity(identifier)

    assert first == second
    assert first.id == identifier


def test_entity_status_starts_active_and_can_be_deactivated_or_reactivated():
    entity = Entity(EntityId.new())

    assert entity.status is EntityStatus.ACTIVE
    entity.deactivate()
    assert entity.status is EntityStatus.INACTIVE
    entity.activate()
    assert entity.status is EntityStatus.ACTIVE


def test_inactive_entity_cannot_be_used_until_reactivated():
    entity = Entity(EntityId.new())
    entity.deactivate()

    with pytest.raises(InactiveEntityError):
        entity.ensure_active()

