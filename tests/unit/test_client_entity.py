import pytest

from assistencia_manager.domain.entities.client import Client
from assistencia_manager.domain.exceptions import DomainValidationError


def test_client_requires_a_non_blank_name():
    with pytest.raises(DomainValidationError):
        Client(name="  ")


def test_client_strips_text_fields_and_preserves_optional_values():
    client = Client(
        name="  Oficina Central  ",
        contacts=("  11999990000  ", " contato@oficina.test "),
        document="  123.456.789-00 ",
        address="  Rua A, 10 ",
        notes="  Cliente antigo ",
    )

    assert client.name == "Oficina Central"
    assert client.contacts == ("11999990000", "contato@oficina.test")
    assert client.document == "123.456.789-00"
    assert client.address == "Rua A, 10"
    assert client.notes == "Cliente antigo"


def test_client_update_keeps_identity_and_validates_name():
    client = Client(name="Oficina Central")
    identifier = client.id

    client.update(name="  Nova Oficina  ", notes=" atualizado ")

    assert client.id == identifier
    assert client.name == "Nova Oficina"
    assert client.notes == "atualizado"
    with pytest.raises(DomainValidationError):
        client.update(name="")

