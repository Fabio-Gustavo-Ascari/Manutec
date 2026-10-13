import pytest

from assistencia_manager.domain.entities.equipment import Equipment
from assistencia_manager.domain.exceptions import DomainValidationError
from assistencia_manager.domain.identifiers import EntityId


def test_equipment_requires_a_client_and_type():
    with pytest.raises(DomainValidationError):
        Equipment(equipment_type="Notebook")

    with pytest.raises(DomainValidationError):
        Equipment(client_id=EntityId.new(), equipment_type="  ")


def test_equipment_normalizes_identifying_fields_and_accessories():
    client_id = EntityId.new()
    equipment = Equipment(
        client_id=client_id,
        equipment_type="  Notebook ",
        brand="  Lenovo ",
        model=" IdeaPad 3 ",
        serial_number=" ABC123 ",
        accessories=(" fonte ", "  bolsa", " "),
    )

    assert equipment.client_id == client_id
    assert equipment.equipment_type == "Notebook"
    assert equipment.brand == "Lenovo"
    assert equipment.model == "IdeaPad 3"
    assert equipment.serial_number == "ABC123"
    assert equipment.accessories == ("fonte", "bolsa")


def test_equipment_update_preserves_identity_and_client_link():
    client_id = EntityId.new()
    equipment = Equipment(client_id=client_id, equipment_type="Notebook")
    identifier = equipment.id

    equipment.update(model="  ThinkPad  ", accessories=(" carregador ",))

    assert equipment.id == identifier
    assert equipment.client_id == client_id
    assert equipment.model == "ThinkPad"
    assert equipment.accessories == ("carregador",)
