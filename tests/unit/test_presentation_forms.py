from __future__ import annotations

import os

import pytest
from PySide6.QtWidgets import QApplication

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="module")
def qapp():
    application = QApplication.instance() or QApplication([])
    yield application
    application.quit()


def test_client_form_shows_message_when_name_is_blank(qapp):
    from assistencia_manager.presentation.pages.clients import ClientForm

    form = ClientForm()
    form.submit()

    assert form.error_message.text() == "Informe o nome do cliente."


def test_client_form_emits_create_command_with_normalized_values(qapp):
    from assistencia_manager.presentation.pages.clients import ClientForm

    form = ClientForm()
    received = []
    form.submitted.connect(received.append)
    form.name_input.setText("  Oficina Central  ")
    form.contacts_input.setText("11 9999; 11 9888")
    form.submit()

    assert len(received) == 1
    assert received[0].name == "Oficina Central"
    assert received[0].contacts == ("11 9999", "11 9888")
    assert form.error_message.text() == ""


def test_equipment_form_validates_client_identifier_and_type(qapp):
    from assistencia_manager.presentation.pages.equipment import EquipmentForm

    form = EquipmentForm()
    form.submit()
    assert form.error_message.text() == "Informe o cliente e o tipo do equipamento."

    form.client_id_input.setText("not-a-uuid")
    form.equipment_type_input.setText("Notebook")
    form.submit()
    assert form.error_message.text() == "Informe um identificador de cliente válido."
